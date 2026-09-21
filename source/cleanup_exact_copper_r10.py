"""Remove only exact zero-length and duplicate copper from the R10 board.

Run this with KiCad's bundled Python, not the system Python.  The native
``pcbnew`` model selects objects by UUID, while the final edit removes only the
matching one-line S-expression records.  This preserves the board's legacy
serialization instead of rewriting the entire file in the current KiCad
format.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "GrandMarquis97_RevA.kicad_pcb"
OUTPUT_JSON = ROOT / "production_review" / "TRACK_CLEANUP_AUDIT.json"
OUTPUT_CSV = ROOT / "production_review" / "TRACK_CLEANUP_AUDIT.csv"
TRACK_LINE = re.compile(r"^  \((segment|via)(?: |\))")
UUID = re.compile(r"\(tstamp ([0-9a-fA-F-]{36})\)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def point(value) -> tuple[int, int]:
    return int(value.x), int(value.y)


def mm(value: int) -> float:
    return round(float(pcbnew.ToMM(value)), 9)


def item_uuid(item) -> str:
    return item.m_Uuid.AsString().lower()


def segment_key(item) -> tuple[object, ...]:
    ends = tuple(sorted((point(item.GetStart()), point(item.GetEnd()))))
    return ("segment", item.GetNetCode(), int(item.GetLayer()), item.GetWidth(), ends)


def via_key(item) -> tuple[object, ...]:
    layers = tuple(int(layer) for layer in item.GetLayerSet().Seq())
    return (
        "via",
        item.GetNetCode(),
        layers,
        item.GetWidth(item.GetLayer()),
        item.GetDrillValue(),
        point(item.GetPosition()),
    )


def copper_key(item) -> tuple[object, ...]:
    return via_key(item) if isinstance(item, pcbnew.PCB_VIA) else segment_key(item)


def is_zero_length(item) -> bool:
    return not isinstance(item, pcbnew.PCB_VIA) and point(item.GetStart()) == point(item.GetEnd())


def describe(item) -> dict[str, object]:
    base: dict[str, object] = {
        "uuid": item_uuid(item),
        "kind": "via" if isinstance(item, pcbnew.PCB_VIA) else "segment",
        "net_code": int(item.GetNetCode()),
        "net": item.GetNetname(),
        "locked": bool(item.IsLocked()),
    }
    if isinstance(item, pcbnew.PCB_VIA):
        position = point(item.GetPosition())
        layer_ids = [int(layer) for layer in item.GetLayerSet().Seq()]
        base.update(
            {
                "position_mm": [mm(position[0]), mm(position[1])],
                "size_mm": mm(item.GetWidth(item.GetLayer())),
                "drill_mm": mm(item.GetDrillValue()),
                "layers": [pcbnew.LayerName(layer) for layer in layer_ids],
            }
        )
    else:
        start = point(item.GetStart())
        end = point(item.GetEnd())
        base.update(
            {
                "start_mm": [mm(start[0]), mm(start[1])],
                "end_mm": [mm(end[0]), mm(end[1])],
                "width_mm": mm(item.GetWidth()),
                "layer": item.GetLayerName(),
            }
        )
    return base


def inventory(board) -> dict[str, int]:
    tracks = list(board.GetTracks())
    footprints = list(board.GetFootprints())
    return {
        "tracks_and_vias": len(tracks),
        "segments": sum(not isinstance(item, pcbnew.PCB_VIA) for item in tracks),
        "vias": sum(isinstance(item, pcbnew.PCB_VIA) for item in tracks),
        "footprints": len(footprints),
        "pads": sum(1 for footprint in footprints for _ in footprint.Pads()),
        "nets": len(board.GetNetsByNetcode()),
    }


def duplicate_counts(items) -> tuple[int, int]:
    counts = collections.Counter(copper_key(item) for item in items)
    return (
        sum(count > 1 for count in counts.values()),
        sum(count - 1 for count in counts.values() if count > 1),
    )


def select_removals(items) -> tuple[dict[str, dict[str, object]], dict[str, int]]:
    removals: dict[str, dict[str, object]] = {}
    zero_items = [item for item in items if is_zero_length(item)]
    for item in zero_items:
        entry = describe(item)
        entry.update({"reason": "zero_length", "survivor_uuid": ""})
        removals[item_uuid(item)] = entry

    groups: dict[tuple[object, ...], list[object]] = collections.defaultdict(list)
    for item in items:
        if not is_zero_length(item):
            groups[copper_key(item)].append(item)

    duplicate_groups = 0
    duplicate_extras = 0
    for group in groups.values():
        if len(group) < 2:
            continue
        duplicate_groups += 1
        duplicate_extras += len(group) - 1
        survivor = sorted(group, key=lambda item: (not item.IsLocked(), item_uuid(item)))[0]
        for item in group:
            if item is survivor:
                continue
            entry = describe(item)
            entry.update(
                {
                    "reason": "exact_duplicate",
                    "survivor_uuid": item_uuid(survivor),
                }
            )
            removals[item_uuid(item)] = entry

    all_groups, all_extras = duplicate_counts(items)
    return removals, {
        "zero_length_segments": len(zero_items),
        "exact_duplicate_groups_all": all_groups,
        "exact_duplicate_extras_all": all_extras,
        "nonzero_duplicate_groups_selected": duplicate_groups,
        "nonzero_duplicate_extras_selected": duplicate_extras,
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = [
        "reason",
        "uuid",
        "survivor_uuid",
        "kind",
        "net_code",
        "net",
        "layer_or_span",
        "width_or_size_mm",
        "start_or_position_mm",
        "end_mm",
        "drill_mm",
        "locked",
    ]
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            is_via = row["kind"] == "via"
            writer.writerow(
                {
                    "reason": row["reason"],
                    "uuid": row["uuid"],
                    "survivor_uuid": row["survivor_uuid"],
                    "kind": row["kind"],
                    "net_code": row["net_code"],
                    "net": row["net"],
                    "layer_or_span": "/".join(row["layers"]) if is_via else row["layer"],
                    "width_or_size_mm": row["size_mm"] if is_via else row["width_mm"],
                    "start_or_position_mm": row["position_mm"] if is_via else row["start_mm"],
                    "end_mm": "" if is_via else row["end_mm"],
                    "drill_mm": row["drill_mm"] if is_via else "",
                    "locked": row["locked"],
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="replace the board after all native-object and reload checks pass",
    )
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(BOARD))
    items = list(board.GetTracks())
    before = inventory(board)
    removals, findings = select_removals(items)

    lines = BOARD.read_text(encoding="utf-8").splitlines(keepends=True)
    track_lines: dict[str, int] = {}
    for index, line in enumerate(lines):
        if not TRACK_LINE.match(line):
            continue
        match = UUID.search(line)
        if not match:
            raise RuntimeError(f"Copper record at line {index + 1} has no UUID")
        uuid = match.group(1).lower()
        if uuid in track_lines:
            raise RuntimeError(f"Copper UUID occurs more than once: {uuid}")
        track_lines[uuid] = index

    native_uuids = {item_uuid(item) for item in items}
    if len(track_lines) != len(items) or set(track_lines) != native_uuids:
        raise RuntimeError(
            "Native/text copper mismatch: "
            f"native={len(native_uuids)}, text={len(track_lines)}, "
            f"native_only={len(native_uuids - set(track_lines))}, "
            f"text_only={len(set(track_lines) - native_uuids)}"
        )
    if not removals:
        print("Board is already clean: no zero-length or exact-duplicate copper found.")
        return

    remove_lines = {track_lines[uuid] for uuid in removals}
    patched_text = "".join(line for index, line in enumerate(lines) if index not in remove_lines)
    original_hash = sha256(BOARD)
    temp_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            prefix=f".{BOARD.stem}.cleanup-",
            suffix=BOARD.suffix,
            dir=BOARD.parent,
            delete=False,
        ) as temporary:
            temporary.write(patched_text)
            temp_name = temporary.name

        staged_board = pcbnew.LoadBoard(temp_name)
        after = inventory(staged_board)
        after_items = list(staged_board.GetTracks())
        after_groups, after_extras = duplicate_counts(after_items)
        after_zero = sum(is_zero_length(item) for item in after_items)

        expected_tracks = before["tracks_and_vias"] - len(removals)
        if after["tracks_and_vias"] != expected_tracks:
            raise RuntimeError(
                f"Reloaded track count {after['tracks_and_vias']} != {expected_tracks}"
            )
        for name in ("footprints", "pads", "nets"):
            if after[name] != before[name]:
                raise RuntimeError(f"Reload changed {name}: {before[name]} -> {after[name]}")
        if after_zero or after_extras:
            raise RuntimeError(
                f"Cleanup incomplete after reload: zero={after_zero}, duplicate_extras={after_extras}"
            )

        rows = sorted(removals.values(), key=lambda row: (row["reason"], row["uuid"]))
        audit = {
            "schema": 1,
            "method": (
                "KiCad pcbnew 10 selected copper UUIDs; only their one-line legacy "
                "S-expression records were removed; the staged board was then reloaded "
                "with pcbnew before replacement."
            ),
            "kicad_version": pcbnew.GetBuildVersion(),
            "board": BOARD.name,
            "before_sha256": original_hash,
            "after_sha256": sha256(Path(temp_name)),
            "before": before,
            "findings": findings,
            "removed_unique_objects": len(removals),
            "removed_locked_objects": sum(bool(row["locked"]) for row in rows),
            "after": after,
            "after_zero_length_segments": after_zero,
            "after_exact_duplicate_groups": after_groups,
            "after_exact_duplicate_extras": after_extras,
            "removed": rows,
        }

        print(json.dumps({key: audit[key] for key in audit if key != "removed"}, indent=2))
        if not args.apply:
            print("Dry run only; pass --apply to replace the board and write audit files.")
            return

        os.replace(temp_name, BOARD)
        temp_name = ""
        OUTPUT_JSON.parent.mkdir(exist_ok=True)
        OUTPUT_JSON.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
        write_csv(OUTPUT_CSV, rows)
        print(f"Applied cleanup and wrote {OUTPUT_JSON.relative_to(ROOT)}")
        print(f"Applied cleanup and wrote {OUTPUT_CSV.relative_to(ROOT)}")
    finally:
        if temp_name and Path(temp_name).exists():
            Path(temp_name).unlink()


if __name__ == "__main__":
    main()
