"""Create and optionally install the reviewed R10 ground-island repair.

The repository board uses KiCad's legacy 20221018 serialization.  KiCad 10
rewrites that file extensively when saving it, so this installer uses pcbnew
only to select and validate native objects.  The actual candidate removes 108
reviewed one-line segment records and inserts 11 segments plus five through
vias immediately before the first top-level zone record.  Preferred DGND
netclass sizes are used on complete routes where the reviewed geometry and
fabrication margin permit them; explicit neckdown routes remain release-held.

Always DRC the exact ``--candidate`` bytes in a full isolated project copy.
Only pass ``--apply-tested-sha256`` after both configured and strict DRC have
accepted that exact SHA-256.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import tempfile
import uuid
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "GrandMarquis97_RevA.kicad_pcb"
AUDIT = ROOT / "production_review" / "GROUND_ISLAND_REPAIR_AUDIT.json"
TRACK_LINE = re.compile(r"^  \((segment|via)(?: |\))")
TRACK_UUID = re.compile(r"\(tstamp ([0-9a-fA-F-]{36})\)")
FORMAT_VERSION = "20221018"
UUID_NAMESPACE = uuid.UUID("4a3f4a8c-b6f1-57f0-9d2e-02ebdc5199b1")

PADLESS_DGND_COUNT = 95
PADLESS_DGND_UUID_SHA256 = "2f78582f22686edb5a64b1e18eec998b540ae941bd9d2789d692696e0ae6531a"
DEAD_DGND_TAILS = {
    "7047c514-955f-4f35-909a-cb70565878d3",
    "86d5cc56-0cdf-4f62-b5b9-2cf05fac3863",
    "a439a729-c400-4bee-b738-3d65e471903d",
    "70ce569b-f739-4852-9a75-e874ea7b59c8",
    "ba944cf3-9995-431c-80ed-5331926f89b0",
    "c5ef23d3-1727-457d-b3d5-7f30370684d5",
    "8af732c9-26aa-4733-bd09-5a7639dd2376",
    "42f5d742-cc88-4e8a-bf8a-9593378a8c37",
    "97283933-d492-4e10-936f-35d173df9893",
    "4e2997e2-9bf9-4d64-b40e-41b35532f6b7",
    "881419c4-25e4-48cf-bf98-9fc0e2c7c0c0",
    "d182c624-39ef-4391-91ff-f3e34f9c64d2",
    "6de335b7-720f-4110-9df3-a124326979f3",
}

ROUTES = [
    {
        "id": "dgnd-d28-plane",
        "net": "DGND",
        "target": "D28.1",
        "finding_ids": ["NATIVE-017", "NATIVE-018"],
        "pieces": [
            ("segment", "B.Cu", (79.0625, 117.95), (72.1, 108.1), 0.25),
            ("segment", "B.Cu", (72.1, 108.1), (70.7, 106.4), 0.25),
            ("via", (70.7, 106.4), 0.6, 0.3),
        ],
    },
    {
        "id": "dgnd-d30-plane",
        "net": "DGND",
        "target": "D30.2",
        "finding_ids": ["NATIVE-021"],
        "pieces": [
            ("segment", "B.Cu", (91.65, 131.0), (92.7, 132.0), 0.6),
            ("via", (92.7, 132.0), 0.8, 0.4),
            ("segment", "In1.Cu", (92.7, 132.0), (95.0, 134.4), 0.6),
        ],
    },
    {
        "id": "dgnd-d26-plane",
        "net": "DGND",
        "target": "D26.1",
        "finding_ids": ["NATIVE-019"],
        "pieces": [
            ("segment", "B.Cu", (88.0625, 120.95), (88.6, 123.4), 0.25),
            ("segment", "B.Cu", (88.6, 123.4), (88.0, 125.9), 0.25),
            ("via", (88.0, 125.9), 0.6, 0.3),
            ("segment", "In1.Cu", (88.0, 125.9), (87.9, 126.0), 0.25),
        ],
    },
    {
        "id": "dgnd-c42-c43-plane",
        "net": "DGND",
        "target": "C42.2+C43.2",
        "finding_ids": ["NATIVE-023"],
        "pieces": [
            ("segment", "F.Cu", (107.553, 40.8833), (107.418, 43.575), 0.6),
        ],
    },
    {
        "id": "dgnd-d31-nt1-plane",
        "net": "DGND",
        "target": "D31.2+NT1.2",
        "finding_ids": ["NATIVE-024", "NATIVE-025"],
        "pieces": [
            ("segment", "F.Cu", (107.67, 27.448), (106.8, 26.7), 0.6),
            ("via", (106.8, 26.7), 0.8, 0.4),
        ],
    },
    {
        "id": "dgnd-d29-d32-plane",
        "net": "DGND",
        "target": "D29.1+D32.1",
        "finding_ids": ["NATIVE-026", "NATIVE-027", "NATIVE-028"],
        "pieces": [
            ("segment", "F.Cu", (116.6075, 30.55), (118.9, 30.2), 0.25),
            ("segment", "F.Cu", (118.9, 30.2), (122.6075, 32.45), 0.25),
        ],
    },
    {
        "id": "pgnd-nt1-zone-plane",
        "net": "PGND",
        "target": "NT1.1 F.Cu zone island",
        "finding_ids": ["NATIVE-037"],
        "pieces": [("via", (101.5, 12.8), 0.6, 0.3)],
    },
]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def values_sha256(values: set[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(values)) + "\n").encode()).hexdigest()


def item_uuid(item) -> str:
    return item.m_Uuid.AsString().lower()


def point(value) -> tuple[int, int]:
    return int(value.x), int(value.y)


def mm(value: int) -> float:
    return round(float(pcbnew.ToMM(value)), 9)


def format_mm(value: float) -> str:
    text = f"{value:.9f}".rstrip("0").rstrip(".")
    return text if text and text != "-0" else "0"


def via_key(item) -> tuple[object, ...]:
    # A through via has no single GetLayer() value; passing F.Cu avoids KiCad's
    # PCB_VIA::GetWidth "called without a layer argument" debug assertion.
    return (
        "via",
        int(item.GetNetCode()),
        point(item.GetPosition()),
        int(item.GetWidth(pcbnew.F_Cu)),
        int(item.GetDrillValue()),
        tuple(int(layer) for layer in item.GetLayerSet().Seq()),
        bool(item.IsLocked()),
    )


def segment_key(item) -> tuple[object, ...]:
    return (
        "segment",
        int(item.GetNetCode()),
        int(item.GetLayer()),
        point(item.GetStart()),
        point(item.GetEnd()),
        int(item.GetWidth()),
        bool(item.IsLocked()),
    )


def copper_key(item) -> tuple[object, ...]:
    return via_key(item) if isinstance(item, pcbnew.PCB_VIA) else segment_key(item)


def geometry_key(item) -> tuple[object, ...]:
    if isinstance(item, pcbnew.PCB_VIA):
        return (
            "via",
            int(item.GetNetCode()),
            point(item.GetPosition()),
            int(item.GetWidth(pcbnew.F_Cu)),
            int(item.GetDrillValue()),
            tuple(int(layer) for layer in item.GetLayerSet().Seq()),
        )
    ends = tuple(sorted((point(item.GetStart()), point(item.GetEnd()))))
    return (
        "segment",
        int(item.GetNetCode()),
        int(item.GetLayer()),
        ends,
        int(item.GetWidth()),
    )


def inventory(board) -> dict[str, int]:
    tracks = list(board.GetTracks())
    footprints = list(board.GetFootprints())
    return {
        "segments": sum(not isinstance(item, pcbnew.PCB_VIA) for item in tracks),
        "vias": sum(isinstance(item, pcbnew.PCB_VIA) for item in tracks),
        "locked_segments": sum(
            not isinstance(item, pcbnew.PCB_VIA) and item.IsLocked() for item in tracks
        ),
        "locked_vias": sum(
            isinstance(item, pcbnew.PCB_VIA) and item.IsLocked() for item in tracks
        ),
        "footprints": len(footprints),
        "pads": sum(1 for footprint in footprints for _ in footprint.Pads()),
        "nets": len(board.GetNetsByNetcode()),
        "zones": len(list(board.Zones())),
    }


def pad_snapshot(board) -> list[tuple[object, ...]]:
    return sorted(
        (
            footprint.GetReference(),
            pad.GetNumber(),
            int(pad.GetNetCode()),
            pad.GetNetname(),
            point(pad.GetPosition()),
        )
        for footprint in board.GetFootprints()
        for pad in footprint.Pads()
    )


def connected_component(board, seed) -> dict[str, object]:
    connected = [
        item
        for item in board.GetConnectivity().GetConnectedItems(seed)
        if isinstance(item, (pcbnew.PAD, pcbnew.PCB_TRACK))
        and item.GetNetCode() == seed.GetNetCode()
    ]
    connected.append(seed)
    return {item_uuid(item): item for item in connected}


def padless_dgnd_segments(board) -> set[str]:
    net = board.FindNet("DGND").GetNetCode()
    items = [
        pad
        for footprint in board.GetFootprints()
        for pad in footprint.Pads()
        if pad.GetNetCode() == net
    ] + [item for item in board.GetTracks() if item.GetNetCode() == net]
    seen: set[str] = set()
    selected: set[str] = set()
    for item in items:
        uid = item_uuid(item)
        if uid in seen:
            continue
        component = connected_component(board, item)
        seen.update(component)
        if any(isinstance(member, pcbnew.PAD) for member in component.values()):
            continue
        if any(isinstance(member, pcbnew.PCB_VIA) for member in component.values()):
            raise RuntimeError("A padless DGND component unexpectedly contains a via")
        selected.update(component)
    return selected


def piece_uuid(route: dict[str, object], index: int, piece: tuple[object, ...]) -> str:
    canonical = json.dumps(
        {"route": route["id"], "index": index, "piece": piece},
        separators=(",", ":"),
    )
    return str(uuid.uuid5(UUID_NAMESPACE, canonical))


def render_piece(
    route: dict[str, object], index: int, piece: tuple[object, ...], net_code: int
) -> tuple[str, dict[str, object]]:
    uid = piece_uuid(route, index, piece)
    if piece[0] == "segment":
        _, layer, start, end, width = piece
        line = (
            f"  (segment (start {format_mm(start[0])} {format_mm(start[1])}) "
            f"(end {format_mm(end[0])} {format_mm(end[1])}) "
            f"(width {format_mm(width)}) (layer \"{layer}\") "
            f"(net {net_code}) (tstamp {uid}))"
        )
        description = {
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
        description = {
            "uuid": uid,
            "kind": "via",
            "net": route["net"],
            "position_mm": list(position),
            "size_mm": size,
            "drill_mm": drill,
            "layers": ["F.Cu", "B.Cu"],
        }
    description.update(
        {
            "route_id": route["id"],
            "target": route["target"],
            "finding_ids": route["finding_ids"],
            "locked": False,
        }
    )
    return line, description


def validate_added(staged, additions: list[dict[str, object]], net_codes: dict[str, int]) -> None:
    items = {item_uuid(item): item for item in staged.GetTracks()}
    for expected in additions:
        item = items.get(expected["uuid"])
        if item is None:
            raise RuntimeError(f"Reload lost added copper {expected['uuid']}")
        if item.GetNetCode() != net_codes[expected["net"]] or item.IsLocked():
            raise RuntimeError(f"Reload changed net/lock state for {expected['uuid']}")
        if expected["kind"] == "segment":
            if isinstance(item, pcbnew.PCB_VIA):
                raise RuntimeError(f"Expected segment {expected['uuid']}")
            actual = {
                "layer": item.GetLayerName(),
                "start_mm": [mm(item.GetStart().x), mm(item.GetStart().y)],
                "end_mm": [mm(item.GetEnd().x), mm(item.GetEnd().y)],
                "width_mm": mm(item.GetWidth()),
            }
            wanted = {key: expected[key] for key in actual}
        else:
            if not isinstance(item, pcbnew.PCB_VIA):
                raise RuntimeError(f"Expected via {expected['uuid']}")
            actual = {
                "position_mm": [mm(item.GetPosition().x), mm(item.GetPosition().y)],
                "size_mm": mm(item.GetWidth(pcbnew.F_Cu)),
                "drill_mm": mm(item.GetDrillValue()),
            }
            wanted = {key: expected[key] for key in actual}
        if actual != wanted:
            raise RuntimeError(
                f"Reload changed {expected['uuid']}: expected {wanted}, got {actual}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument(
        "--source-board",
        type=Path,
        default=BOARD,
        help="reviewed pre-repair board; defaults to the repository board",
    )
    parser.add_argument(
        "--apply-tested-sha256",
        help="install only if the recomputed candidate exactly matches this tested SHA-256",
    )
    parser.add_argument(
        "--expected-active-sha256",
        help="required when applying a candidate built from an isolated source board",
    )
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    source_board = args.source_board.resolve()
    if candidate == BOARD.resolve():
        raise SystemExit("Refusing to use the repository board as the candidate path")
    if candidate == source_board:
        raise SystemExit("Refusing to overwrite the source board with the candidate")

    board = pcbnew.LoadBoard(str(source_board))
    before = inventory(board)
    before_pads = pad_snapshot(board)
    before_items = list(board.GetTracks())
    before_by_uuid = {item_uuid(item): item for item in before_items}
    if len(before_by_uuid) != len(before_items):
        raise RuntimeError("Native copper UUIDs are not unique")

    net_codes = {name: int(board.FindNet(name).GetNetCode()) for name in ("DGND", "PGND")}
    if net_codes != {"DGND": 66, "PGND": 124}:
        raise RuntimeError(f"Unexpected ground net codes: {net_codes}")

    additions_rendered: list[str] = []
    additions: list[dict[str, object]] = []
    for route in ROUTES:
        for index, piece in enumerate(route["pieces"]):
            line, description = render_piece(route, index, piece, net_codes[route["net"]])
            additions_rendered.append(line)
            additions.append(description)
    added_uuids = {entry["uuid"] for entry in additions}
    if added_uuids & set(before_by_uuid):
        if added_uuids <= set(before_by_uuid):
            raise SystemExit("Ground-island repair is already installed")
        raise RuntimeError("Only part of the deterministic repair UUID set is present")

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.BuildConnectivity()
    padless = padless_dgnd_segments(board)
    if len(padless) != PADLESS_DGND_COUNT or values_sha256(padless) != PADLESS_DGND_UUID_SHA256:
        raise RuntimeError(
            "Padless DGND selection differs from the reviewed set: "
            f"count={len(padless)}, sha256={values_sha256(padless)}"
        )
    removals = padless | DEAD_DGND_TAILS
    if len(removals) != 108 or not removals <= set(before_by_uuid):
        raise RuntimeError("Reviewed removal UUID set is incomplete")
    for uid in removals:
        item = before_by_uuid[uid]
        if (
            isinstance(item, pcbnew.PCB_VIA)
            or item.GetNetname() != "DGND"
            or item.IsLocked()
        ):
            raise RuntimeError(f"Removal invariant failed for {uid}")

    raw = source_board.read_bytes()
    text = raw.decode("utf-8")
    version = re.search(r"\(version (\d+)\)", text[:512])
    if not version or version.group(1) != FORMAT_VERSION:
        raise RuntimeError("Board is not the reviewed legacy 20221018 serialization")
    newline = "\r\n" if b"\r\n" in raw[:4096] else "\n"
    lines = text.splitlines(keepends=True)
    copper_lines: dict[str, int] = {}
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
        raise RuntimeError("A deterministic repair UUID collides with an existing board UUID")

    insertion = next(
        (index for index, line in enumerate(lines) if line.startswith("  (zone ")),
        None,
    )
    if insertion is None:
        raise RuntimeError("No top-level zone insertion point found")
    if any(TRACK_LINE.match(line) for line in lines[insertion:]):
        raise RuntimeError("Copper records unexpectedly occur after the first top-level zone")

    removal_lines = {copper_lines[uid] for uid in removals}
    output_lines = [line for index, line in enumerate(lines[:insertion]) if index not in removal_lines]
    output_lines.extend(line + newline for line in additions_rendered)
    output_lines.extend(lines[insertion:])
    candidate_bytes = "".join(output_lines).encode("utf-8")

    candidate.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{candidate.stem}.ground-repair-",
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
    expected_after["segments"] = before["segments"] - len(removals) + sum(
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
    if removals & set(after_by_uuid) or not added_uuids <= set(after_by_uuid):
        raise RuntimeError("Reloaded copper UUID delta differs from the manifest")
    for uid, original in before_by_uuid.items():
        if uid in removals:
            continue
        if uid not in after_by_uuid or copper_key(after_by_uuid[uid]) != copper_key(original):
            raise RuntimeError(f"Existing copper changed unexpectedly: {uid}")
    validate_added(staged, additions, net_codes)

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
            f"Candidate introduced invalid copper: zero={zero_length}, duplicate_extras={duplicate_extras}"
        )

    candidate_hash = file_sha256(candidate)
    audit = {
        "schema": 1,
        "method": (
            "pcbnew selected and validated reviewed native objects; only their legacy "
            "one-line records were removed or inserted; the staged candidate was reloaded "
            "without saving through KiCad 10."
        ),
        "kicad_version": pcbnew.GetBuildVersion(),
        "board_format": FORMAT_VERSION,
        "board": source_board.name,
        "source_board": source_board.name,
        "before_sha256": file_sha256(source_board),
        "candidate_sha256": candidate_hash,
        "before": before,
        "after": after,
        "pad_net_assignments_unchanged": True,
        "zero_length_segments_after": zero_length,
        "exact_duplicate_extras_after": duplicate_extras,
        "removed_padless_dgnd_segments": sorted(padless),
        "removed_dead_dgnd_tail_segments": sorted(DEAD_DGND_TAILS),
        "added": additions,
        "repaired_targets": [route["target"] for route in ROUTES],
        "remaining_ground_blocks": [
            {
                "target": "D27.1",
                "net": "DGND",
                "reason": "no 0.25 mm escape and legal 0.60/0.30 mm through-via path without rerouting adjacent signals",
            },
            {
                "target": "R80.2 F.Cu zone island",
                "net": "PGND",
                "reason": "no legal through-via or F.Cu escape without rerouting existing coil/control copper",
            },
        ],
        "preferred_sizing_review": {
            "DGND": {
                "netclass": "Rails_unverified",
                "preferred_track_width_mm": 0.6,
                "preferred_via_size_mm": 0.8,
                "preferred_via_drill_mm": 0.4,
            },
            "PGND": {
                "netclass": "Shared_power_unverified",
                "preferred_track_width_mm": 4.0,
                "preferred_via_size_mm": 0.8,
                "preferred_via_drill_mm": 0.4,
            },
            "installed_summary": {
                "DGND_segments_at_preferred": 4,
                "DGND_geometry_limited_segments_0_25_mm": 7,
                "DGND_vias_at_preferred": 2,
                "DGND_geometry_limited_vias_0_60_0_30_mm": 2,
                "PGND_geometry_limited_vias_0_60_0_30_mm": 1,
            },
            "exceptions": [
                {
                    "target": "D28.1",
                    "installed": "two 0.25 mm B.Cu segments and one 0.60/0.30 mm via",
                    "preferred": "0.60 mm segments and 0.80/0.40 mm via",
                    "collision_boundaries_mm": [0.258745, 0.560741],
                    "via_preferred_nominal_headroom_mm": 0.004,
                    "via_disposition": (
                        "The preferred via passes nominal DRC but is retained at the "
                        "existing standard size because fabricator tolerances are unselected."
                    ),
                    "blockers": [
                        "D28.2 VCC_5 pad 03a14690-9dd1-498c-92f6-8434aa00c99c",
                        "TRANS_SS2 track 5d9e4ea2-3c51-494e-99e2-2fdd507558f5",
                    ],
                },
                {
                    "target": "D26.1",
                    "installed": "three 0.25 mm segments and one 0.60/0.30 mm via",
                    "preferred": "0.60 mm segments and 0.80/0.40 mm via",
                    "collision_boundaries_mm": [0.547244, 0.360472, 0.736478],
                    "partial_upgrade_disposition": (
                        "The short In1.Cu plane landing accepts 0.60 mm, but partial "
                        "widening would not remove the B.Cu/via bottleneck."
                    ),
                    "blockers": [
                        "SPARE_PE0 via 8fb3f187-fad0-4d71-a691-014c3fd0a2ec",
                        "VCC_5 track 09186073-4b16-481d-92f7-98f24ab01a0e",
                    ],
                },
                {
                    "target": "D29.1+D32.1",
                    "installed": "two 0.25 mm F.Cu segments",
                    "preferred": "0.60 mm",
                    "collision_boundaries_mm": [0.454071, 0.427629],
                    "blockers": [
                        "FLEX_LOGIC track 54b337e3-30f3-44df-b741-de0b0fcab178"
                    ],
                },
                {
                    "target": "NT1.1 F.Cu zone island",
                    "installed": "one 0.60/0.30 mm PGND via",
                    "preferred": "0.80/0.40 mm via",
                    "collision_boundary_mm": 0.698002,
                    "blockers": [
                        "INJECTOR_2 track c58a6895-ee1e-42d0-926e-ac22330cb888",
                        "INJECTOR_2 track f8017d3c-a1af-4643-af6a-1cf9bc56ec76",
                    ],
                },
            ],
            "qualification_status": (
                "Geometry-limited sub-class ground neckdowns remain unqualified "
                "and release-held pending current/return-path review or local rerouting."
            ),
        },
    }
    print(
        json.dumps(
            {
                "candidate": str(candidate),
                "candidate_sha256": candidate_hash,
                "before": before,
                "after": after,
                "removed_segments": len(removals),
                "added_segments": sum(entry["kind"] == "segment" for entry in additions),
                "added_vias": sum(entry["kind"] == "via" for entry in additions),
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
            f"Tested SHA-256 {args.apply_tested_sha256!r} does not match candidate {candidate_hash}"
        )
    active_before = file_sha256(BOARD)
    if source_board != BOARD.resolve():
        expected_active = (args.expected_active_sha256 or "").lower()
        if not re.fullmatch(r"[0-9a-f]{64}", expected_active):
            raise RuntimeError(
                "--expected-active-sha256 is required when applying from an isolated source board"
            )
        if active_before != expected_active:
            raise RuntimeError(
                f"Active board SHA-256 {active_before} != expected {expected_active}"
            )
    elif args.expected_active_sha256 and active_before != args.expected_active_sha256.lower():
        raise RuntimeError(
            f"Active board SHA-256 {active_before} != expected {args.expected_active_sha256.lower()}"
        )
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{BOARD.stem}.ground-repair-",
        suffix=BOARD.suffix,
        dir=BOARD.parent,
        delete=False,
    ) as temporary:
        temporary.write(candidate_bytes)
        install_name = Path(temporary.name)
    if file_sha256(install_name) != tested:
        install_name.unlink(missing_ok=True)
        raise RuntimeError("Same-directory install staging hash differs from tested candidate")
    os.replace(install_name, BOARD)
    audit["installation_guard_active_sha256"] = active_before
    audit["installed_sha256"] = file_sha256(BOARD)
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(f"Installed exact tested bytes and wrote {AUDIT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
