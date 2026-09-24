"""Create and optionally install the reviewed R10 D27 ground repair.

D27 is the BAT54S clamp for DATALOG_LOGIC.  This repair locally reroutes one
SPARE_PM2 segment and one HEATER_G1 segment at the current 0.25 mm signal
target, then gives D27.1 a short 0.25 mm B.Cu return and a 0.60/0.30 mm
through via into the existing In4/In6 DGND planes.

The board uses KiCad's legacy 20221018 serialization.  KiCad 10 rewrites that
file extensively when saving it, so this installer uses pcbnew for native
validation while changing only reviewed one-line copper records.  Always DRC
the exact ``--candidate`` bytes in isolated full-project copies.  Only pass
``--apply-tested-sha256`` after configured and strict DRC accept that SHA-256.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import tempfile
import uuid
from pathlib import Path

import pcbnew

from repair_ground_islands_r10 import (
    copper_key,
    file_sha256,
    format_mm,
    geometry_key,
    inventory,
    item_uuid,
    pad_snapshot,
    point,
)


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "GrandMarquis97_RevA.kicad_pcb"
AUDIT = ROOT / "production_review" / "D27_GROUND_REPAIR_AUDIT.json"
FORMAT_VERSION = "20221018"
REVIEWED_SOURCE_SHA256 = "1b387eafbcfb576f3ef0c462b303d157d2e03def681219a8f3fcaa12acb7f529"
TRACK_LINE = re.compile(r"^  \((segment|via)(?: |\))")
TRACK_UUID = re.compile(r"\(tstamp ([0-9a-fA-F-]{36})\)")
UUID_NAMESPACE = uuid.UUID("cf9cff89-f742-5d61-a3cf-c1c53247525b")

D27_PAD_UUID = "586be20a-644d-4679-86c9-3e656d83b49d"
PAD_GROUPS = {
    "SPARE_PM2": {
        "d4e9d9d3-c242-4da4-9292-b0bad9b14348",
        "fe247194-0a87-4934-95b1-cfe3954e42a5",
    },
    "HEATER_G1": {
        "162f2f8e-3337-4ece-95ee-f2a14298aaaa",
        "1c2e9867-9a7e-4d84-8da0-df89ecca887a",
        "ce9ad774-9e96-4c68-87ef-8b70dba344a0",
    },
}
REMOVALS = {
    "bdacaac7-4d84-448b-b9d1-f5508d5000eb": {
        "net": "SPARE_PM2",
        "layer": "In2.Cu",
        "start_end_mm": ((78.7, 128.8), (77.2, 125.1)),
        "width_mm": 0.2,
    },
    "9fa0850f-16d9-4b70-b5bd-01a0172e1459": {
        "net": "HEATER_G1",
        "layer": "In5.Cu",
        "start_end_mm": ((78.7, 125.3), (78.7, 128.1)),
        "width_mm": 0.2,
    },
}
ROUTES = [
    {
        "id": "spare-pm2-d27-clearance",
        "net": "SPARE_PM2",
        "target": "preserve J101.27 to J130.18",
        "pieces": [
            ("segment", "In2.Cu", (78.7, 128.8), (77.9, 127.8), 0.25),
            ("segment", "In2.Cu", (77.9, 127.8), (77.2, 125.1), 0.25),
        ],
    },
    {
        "id": "heater-g1-d27-clearance",
        "net": "HEATER_G1",
        "target": "preserve Q26.1, R108.2, and R109.1 connectivity",
        "pieces": [
            ("segment", "In5.Cu", (78.7, 125.3), (77.8, 127.0), 0.25),
            ("segment", "In5.Cu", (77.8, 127.0), (78.0, 128.15), 0.25),
            ("segment", "In5.Cu", (78.0, 128.15), (78.7, 128.1), 0.25),
        ],
    },
    {
        "id": "dgnd-d27-plane",
        "net": "DGND",
        "target": "D27.1",
        "finding_ids": ["NATIVE-018"],
        "pieces": [
            ("segment", "B.Cu", (79.0625, 126.95), (78.65, 127.4), 0.25),
            ("via", (78.65, 127.4), 0.6, 0.3),
        ],
    },
]


def mm_point(value) -> tuple[float, float]:
    return round(float(pcbnew.ToMM(value.x)), 9), round(float(pcbnew.ToMM(value.y)), 9)


def find_item(board, uid: str):
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if item_uuid(pad) == uid:
                return pad
    for item in board.GetTracks():
        if item_uuid(item) == uid:
            return item
    raise RuntimeError(f"Native item not found: {uid}")


def group_connected(board, pad_uuids: set[str]) -> bool:
    pads = [find_item(board, uid) for uid in sorted(pad_uuids)]
    board.BuildConnectivity()
    connected = {
        item_uuid(item)
        for item in board.GetConnectivity().GetConnectedItems(pads[0])
        if isinstance(item, (pcbnew.PAD, pcbnew.PCB_TRACK))
    }
    return all(item_uuid(pad) in connected for pad in pads[1:])


def validate_removals(board, by_uuid: dict[str, object]) -> None:
    for uid, expected in REMOVALS.items():
        item = by_uuid.get(uid)
        if item is None or isinstance(item, pcbnew.PCB_VIA):
            raise RuntimeError(f"Reviewed reroute segment missing: {uid}")
        actual_ends = tuple(sorted((mm_point(item.GetStart()), mm_point(item.GetEnd()))))
        wanted_ends = tuple(sorted(expected["start_end_mm"]))
        if (
            item.GetNetname() != expected["net"]
            or item.GetLayerName() != expected["layer"]
            or round(pcbnew.ToMM(item.GetWidth()), 9) != expected["width_mm"]
            or item.IsLocked()
            or actual_ends != wanted_ends
        ):
            raise RuntimeError(f"Reviewed reroute invariant failed for {uid}")


def piece_uuid(route: dict[str, object], index: int, piece: tuple[object, ...]) -> str:
    canonical = json.dumps(
        {"route": route["id"], "index": index, "piece": piece},
        separators=(",", ":"),
    )
    return str(uuid.uuid5(UUID_NAMESPACE, canonical))


def render_piece(route, index, piece, net_code):
    uid = piece_uuid(route, index, piece)
    if piece[0] == "segment":
        _, layer, start, end, width = piece
        line = (
            f"  (segment (start {format_mm(start[0])} {format_mm(start[1])}) "
            f"(end {format_mm(end[0])} {format_mm(end[1])}) "
            f"(width {format_mm(width)}) (layer \"{layer}\") "
            f"(net {net_code}) (tstamp {uid}))"
        )
        entry = {
            "uuid": uid,
            "kind": "segment",
            "net": route["net"],
            "layer": layer,
            "start_mm": list(start),
            "end_mm": list(end),
            "width_mm": width,
        }
    else:
        _, position, size, drill = piece
        line = (
            f"  (via (at {format_mm(position[0])} {format_mm(position[1])}) "
            f"(size {format_mm(size)}) (drill {format_mm(drill)}) "
            f"(layers \"F.Cu\" \"B.Cu\") (net {net_code}) (tstamp {uid}))"
        )
        entry = {
            "uuid": uid,
            "kind": "via",
            "net": route["net"],
            "position_mm": list(position),
            "size_mm": size,
            "drill_mm": drill,
            "layers": ["F.Cu", "B.Cu"],
        }
    entry.update(
        {
            "route_id": route["id"],
            "target": route["target"],
            "finding_ids": route.get("finding_ids", []),
            "locked": False,
        }
    )
    return line, entry


def validate_added(board, additions, net_codes) -> None:
    by_uuid = {item_uuid(item): item for item in board.GetTracks()}
    for expected in additions:
        item = by_uuid.get(expected["uuid"])
        if (
            item is None
            or item.GetNetCode() != net_codes[expected["net"]]
            or item.IsLocked()
        ):
            raise RuntimeError(f"Reload changed added copper {expected['uuid']}")
        if expected["kind"] == "segment":
            if isinstance(item, pcbnew.PCB_VIA):
                raise RuntimeError(f"Expected segment {expected['uuid']}")
            actual = {
                "layer": item.GetLayerName(),
                "start_mm": list(mm_point(item.GetStart())),
                "end_mm": list(mm_point(item.GetEnd())),
                "width_mm": round(pcbnew.ToMM(item.GetWidth()), 9),
            }
        else:
            if not isinstance(item, pcbnew.PCB_VIA):
                raise RuntimeError(f"Expected via {expected['uuid']}")
            actual = {
                "position_mm": list(mm_point(item.GetPosition())),
                "size_mm": round(pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)), 9),
                "drill_mm": round(pcbnew.ToMM(item.GetDrillValue()), 9),
            }
        wanted = {key: expected[key] for key in actual}
        if actual != wanted:
            raise RuntimeError(
                f"Reload changed {expected['uuid']}: expected {wanted}, got {actual}"
            )


def validate_plane_landing(board) -> list[str]:
    position = pcbnew.VECTOR2I(pcbnew.FromMM(78.65), pcbnew.FromMM(127.4))
    layers = sorted(
        {
            board.GetLayerName(layer)
            for zone in board.Zones()
            if zone.GetNetname() == "DGND"
            for layer in zone.GetLayerSet().Seq()
            if zone.HitTestFilledArea(layer, position)
        }
    )
    if not {"In4.Cu", "In6.Cu"} <= set(layers):
        raise RuntimeError(f"D27 via misses reviewed DGND planes: {layers}")
    return layers


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--source-board", type=Path, default=BOARD)
    parser.add_argument("--apply-tested-sha256")
    parser.add_argument("--expected-active-sha256")
    args = parser.parse_args()

    candidate = args.candidate.resolve()
    source_board = args.source_board.resolve()
    if candidate in {BOARD.resolve(), source_board}:
        raise SystemExit("Refusing to overwrite a source or active board as the candidate")
    source_hash = file_sha256(source_board)
    if source_hash != REVIEWED_SOURCE_SHA256:
        raise RuntimeError(
            f"Source SHA-256 {source_hash} is not reviewed {REVIEWED_SOURCE_SHA256}"
        )

    board = pcbnew.LoadBoard(str(source_board))
    before = inventory(board)
    before_pads = pad_snapshot(board)
    before_items = list(board.GetTracks())
    before_by_uuid = {item_uuid(item): item for item in before_items}
    if len(before_items) != len(before_by_uuid):
        raise RuntimeError("Native copper UUIDs are not unique")
    validate_removals(board, before_by_uuid)
    for name, pad_uuids in PAD_GROUPS.items():
        if not group_connected(board, pad_uuids):
            raise RuntimeError(f"{name} pads are not connected before the reroute")

    net_codes = {
        name: int(board.FindNet(name).GetNetCode())
        for name in ("DGND", "HEATER_G1", "SPARE_PM2")
    }
    if net_codes != {"DGND": 66, "HEATER_G1": 81, "SPARE_PM2": 137}:
        raise RuntimeError(f"Unexpected reviewed net codes: {net_codes}")

    rendered = []
    additions = []
    for route in ROUTES:
        for index, piece in enumerate(route["pieces"]):
            line, entry = render_piece(route, index, piece, net_codes[route["net"]])
            rendered.append(line)
            additions.append(entry)
    added_uuids = {entry["uuid"] for entry in additions}
    if added_uuids & set(before_by_uuid):
        if added_uuids <= set(before_by_uuid):
            raise SystemExit("D27 ground repair is already installed")
        raise RuntimeError("Only part of the deterministic D27 repair is present")

    raw = source_board.read_bytes()
    text = raw.decode("utf-8")
    version = re.search(r"\(version (\d+)\)", text[:512])
    if not version or version.group(1) != FORMAT_VERSION:
        raise RuntimeError("Board is not the reviewed legacy 20221018 serialization")
    newline = "\r\n" if b"\r\n" in raw[:4096] else "\n"
    lines = text.splitlines(keepends=True)
    copper_lines = {}
    for line_number, line in enumerate(lines):
        if not TRACK_LINE.match(line):
            continue
        match = TRACK_UUID.search(line)
        if not match:
            raise RuntimeError(f"Copper record at line {line_number + 1} has no UUID")
        uid = match.group(1).lower()
        if uid in copper_lines:
            raise RuntimeError(f"Copper UUID occurs more than once: {uid}")
        copper_lines[uid] = line_number
    if set(copper_lines) != set(before_by_uuid):
        raise RuntimeError("Native/text copper UUID inventories differ")
    if added_uuids & set(re.findall(r"[0-9a-fA-F-]{36}", text)):
        raise RuntimeError("A deterministic D27 repair UUID collides with the board")

    insertion = next(
        (index for index, line in enumerate(lines) if line.startswith("  (zone ")),
        None,
    )
    if insertion is None or any(TRACK_LINE.match(line) for line in lines[insertion:]):
        raise RuntimeError("Legacy copper insertion boundary is not as reviewed")
    removal_lines = {copper_lines[uid] for uid in REMOVALS}
    output = [line for index, line in enumerate(lines[:insertion]) if index not in removal_lines]
    output.extend(line + newline for line in rendered)
    output.extend(lines[insertion:])
    candidate_bytes = "".join(output).encode("utf-8")

    candidate.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{candidate.stem}.d27-repair-",
        suffix=candidate.suffix,
        dir=candidate.parent,
        delete=False,
    ) as temporary:
        temporary.write(candidate_bytes)
        temporary_name = Path(temporary.name)
    os.replace(temporary_name, candidate)

    staged = pcbnew.LoadBoard(str(candidate))
    after = inventory(staged)
    expected_after = dict(before)
    expected_after["segments"] = before["segments"] - len(REMOVALS) + sum(
        entry["kind"] == "segment" for entry in additions
    )
    expected_after["vias"] = before["vias"] + sum(
        entry["kind"] == "via" for entry in additions
    )
    if after != expected_after:
        raise RuntimeError(f"Reloaded inventory mismatch: expected {expected_after}, got {after}")
    if pad_snapshot(staged) != before_pads:
        raise RuntimeError("Footprint pad/net mapping changed")

    after_items = list(staged.GetTracks())
    after_by_uuid = {item_uuid(item): item for item in after_items}
    if set(REMOVALS) & set(after_by_uuid) or not added_uuids <= set(after_by_uuid):
        raise RuntimeError("Reloaded copper UUID delta differs from the manifest")
    for uid, original in before_by_uuid.items():
        if uid in REMOVALS:
            continue
        if uid not in after_by_uuid or copper_key(after_by_uuid[uid]) != copper_key(original):
            raise RuntimeError(f"Existing copper changed unexpectedly: {uid}")
    validate_added(staged, additions, net_codes)

    pcbnew.ZONE_FILLER(staged).Fill(staged.Zones())
    plane_layers = validate_plane_landing(staged)
    for name, pad_uuids in PAD_GROUPS.items():
        if not group_connected(staged, pad_uuids):
            raise RuntimeError(f"D27 repair disconnected {name}")
    d27_pad = find_item(staged, D27_PAD_UUID)
    connected_d27 = {
        item_uuid(item)
        for item in staged.GetConnectivity().GetConnectedItems(d27_pad)
        if isinstance(item, (pcbnew.PAD, pcbnew.PCB_TRACK))
    }
    d27_additions = {
        entry["uuid"] for entry in additions if entry["route_id"] == "dgnd-d27-plane"
    }
    if not d27_additions <= connected_d27:
        raise RuntimeError("Added D27 route is not natively connected to D27.1")

    zero_length = sum(
        not isinstance(item, pcbnew.PCB_VIA) and point(item.GetStart()) == point(item.GetEnd())
        for item in after_items
    )
    duplicate_extras = sum(
        count - 1
        for count in collections.Counter(geometry_key(item) for item in after_items).values()
        if count > 1
    )
    if zero_length or duplicate_extras:
        raise RuntimeError(
            f"Candidate introduced invalid copper: zero={zero_length}, duplicate={duplicate_extras}"
        )

    candidate_hash = file_sha256(candidate)
    audit = {
        "schema": 1,
        "method": (
            "pcbnew validated native objects, pad connectivity, and plane overlap; only two "
            "reviewed legacy segment records were removed and deterministic copper records "
            "inserted; the candidate was reloaded without a KiCad 10 save"
        ),
        "kicad_version": pcbnew.GetBuildVersion(),
        "board_format": FORMAT_VERSION,
        "board": BOARD.name,
        "source_sha256": source_hash,
        "candidate_sha256": candidate_hash,
        "before": before,
        "after": after,
        "pad_net_assignments_unchanged": True,
        "preserved_pad_connectivity": sorted(PAD_GROUPS),
        "removed": [{"uuid": uid, **entry} for uid, entry in REMOVALS.items()],
        "added": additions,
        "repaired_target": "D27.1",
        "finding_id": "NATIVE-018",
        "via_dgnd_plane_layers": plane_layers,
        "sizing_disposition": {
            "signal_reroutes": "0.25 mm current signal target",
            "D27_function": (
                "BAT54S DATALOG_LOGIC transient clamp return; not an injector, ignition, "
                "or other load-current path"
            ),
            "D27_installed": "0.25 mm B.Cu segment and 0.60/0.30 mm through via",
            "preferred_DGND_class": "0.60 mm segment and 0.80/0.40 mm via",
            "D27_exception": (
                "geometry-limited local neckdown matching the reviewed D26/D28 clamp-return "
                "precedent; release-held pending transient and component qualification"
            ),
            "fabrication_margin_hold": (
                "the 0.60 mm via is nominally at the 0.250 mm clearance boundary to existing "
                "F.Cu SPARE_PM2 track dead8b89-46fc-4819-b211-3673a6696172; retain the "
                "stackup/fabricator-tolerance hold"
            ),
        },
        "remaining_ground_block": {
            "target": "R80.2 F.Cu zone island",
            "net": "PGND",
            "reason": "requires a separate local reroute around coil/control copper",
        },
        "zero_length_segments_after": zero_length,
        "exact_duplicate_extras_after": duplicate_extras,
    }
    print(
        json.dumps(
            {
                "candidate": str(candidate),
                "candidate_sha256": candidate_hash,
                "before": before,
                "after": after,
                "removed_segments": len(REMOVALS),
                "added_segments": sum(entry["kind"] == "segment" for entry in additions),
                "added_vias": sum(entry["kind"] == "via" for entry in additions),
                "via_dgnd_plane_layers": plane_layers,
                "preserved_pad_connectivity": sorted(PAD_GROUPS),
            },
            indent=2,
        )
    )

    if not args.apply_tested_sha256:
        print("Candidate only; DRC these exact bytes before applying.")
        return
    tested = args.apply_tested_sha256.lower()
    if not re.fullmatch(r"[0-9a-f]{64}", tested) or tested != candidate_hash:
        raise RuntimeError(
            f"Tested SHA-256 {args.apply_tested_sha256!r} does not match {candidate_hash}"
        )
    active_before = file_sha256(BOARD)
    expected_active = (args.expected_active_sha256 or REVIEWED_SOURCE_SHA256).lower()
    if active_before != expected_active:
        raise RuntimeError(
            f"Active board SHA-256 {active_before} != expected {expected_active}"
        )
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{BOARD.stem}.d27-repair-",
        suffix=BOARD.suffix,
        dir=BOARD.parent,
        delete=False,
    ) as temporary:
        temporary.write(candidate_bytes)
        install_name = Path(temporary.name)
    if file_sha256(install_name) != tested:
        install_name.unlink(missing_ok=True)
        raise RuntimeError("Same-directory staging hash differs from tested candidate")
    os.replace(install_name, BOARD)
    audit["installation_guard_active_sha256"] = active_before
    audit["installed_sha256"] = file_sha256(BOARD)
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(f"Installed exact tested bytes and wrote {AUDIT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
