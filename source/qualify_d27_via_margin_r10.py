"""Create and optionally install the reviewed R10 D27 via-margin upgrade.

The first D27 repair closed the DGND open, but its 0.60/0.30 mm via sat at
the 0.250 mm rule boundary to an F.Cu signal.  This follow-on moves the via,
increases its pad to 0.65 mm while retaining the standard 0.30 mm drill,
restores the short DGND return to the 0.60 mm rail-class width, and moves only
the local HEATER_G1 escape that blocks the improved site.

The board uses KiCad's legacy 20221018 serialization.  KiCad 10 rewrites that
file extensively when saving it, so this installer validates native objects
while changing only reviewed one-line copper records.  DRC the exact
``--candidate`` bytes in isolated full-project copies, then pass their SHA-256
to ``--apply-tested-sha256``.
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import os
import re
import tempfile
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
AUDIT = ROOT / "production_review" / "D27_VIA_MARGIN_AUDIT.json"
FORMAT_VERSION = "20221018"
REVIEWED_SOURCE_SHA256 = "812efbeb56429a5944ccdd86b9af773ec80edf383730570cbbbdbac23a657999"
TRACK_LINE = re.compile(r"^  \((segment|via)(?: |\))")
TRACK_UUID = re.compile(r"\(tstamp ([0-9a-fA-F-]{36})\)")

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
    "027928f8-3419-55bb-8db7-76c5ae338d97": {
        "kind": "segment",
        "net": "DGND",
        "layer": "B.Cu",
        "start_end_mm": ((79.0625, 126.95), (78.65, 127.4)),
        "width_mm": 0.25,
    },
    "60bd5d23-d56a-596f-acb4-8d2bd59c5329": {
        "kind": "via",
        "net": "DGND",
        "position_mm": (78.65, 127.4),
        "size_mm": 0.6,
        "drill_mm": 0.3,
    },
    "03ebb12e-c938-5d66-a863-ad574af7d876": {
        "kind": "segment",
        "net": "HEATER_G1",
        "layer": "In5.Cu",
        "start_end_mm": ((78.7, 125.3), (77.8, 127.0)),
        "width_mm": 0.25,
    },
    "8854b4af-2d2f-5f07-a671-90a3d518b5c0": {
        "kind": "segment",
        "net": "HEATER_G1",
        "layer": "In5.Cu",
        "start_end_mm": ((77.8, 127.0), (78.0, 128.15)),
        "width_mm": 0.25,
    },
    "9231463b-c692-5143-9722-c3736261e30e": {
        "kind": "segment",
        "net": "HEATER_G1",
        "layer": "In5.Cu",
        "start_end_mm": ((78.0, 128.15), (78.7, 128.1)),
        "width_mm": 0.25,
    },
    "ca2896ea-adad-436d-822d-914d3dc9cdb6": {
        "kind": "segment",
        "net": "HEATER_G1",
        "layer": "In5.Cu",
        "start_end_mm": ((78.7, 128.1), (78.6, 128.2)),
        "width_mm": 0.2,
    },
    "a425f412-fdb6-4eab-af62-1bbdf97ec27b": {
        "kind": "segment",
        "net": "HEATER_G1",
        "layer": "In5.Cu",
        "start_end_mm": ((78.6, 128.2), (78.6, 129.6)),
        "width_mm": 0.2,
    },
}

ADDITIONS = [
    {
        "uuid": "f31712c3-5545-564d-9eab-d68837580d59",
        "kind": "segment",
        "net": "HEATER_G1",
        "layer": "In5.Cu",
        "start_mm": (78.7, 125.3),
        "end_mm": (77.5, 126.5),
        "width_mm": 0.25,
        "route_id": "heater-g1-d27-via-margin",
    },
    {
        "uuid": "b28f999d-18cb-5065-94cd-9f4fbcd0f211",
        "kind": "segment",
        "net": "HEATER_G1",
        "layer": "In5.Cu",
        "start_mm": (77.5, 126.5),
        "end_mm": (77.5, 128.5),
        "width_mm": 0.25,
        "route_id": "heater-g1-d27-via-margin",
    },
    {
        "uuid": "fb1eb763-b336-5007-bd50-ac36e536861e",
        "kind": "segment",
        "net": "HEATER_G1",
        "layer": "In5.Cu",
        "start_mm": (77.5, 128.5),
        "end_mm": (78.6, 129.6),
        "width_mm": 0.25,
        "route_id": "heater-g1-d27-via-margin",
    },
    {
        "uuid": "744e5601-cda5-5f4a-8554-33b7cfdfc230",
        "kind": "segment",
        "net": "DGND",
        "layer": "B.Cu",
        "start_mm": (79.0625, 126.95),
        "end_mm": (78.735, 127.575),
        "width_mm": 0.6,
        "route_id": "dgnd-d27-via-margin",
    },
    {
        "uuid": "11d82c0e-fa6b-56b7-ba61-79a3d4f3623e",
        "kind": "via",
        "net": "DGND",
        "position_mm": (78.735, 127.575),
        "size_mm": 0.65,
        "drill_mm": 0.3,
        "layers": ("F.Cu", "B.Cu"),
        "route_id": "dgnd-d27-via-margin",
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
        if item is None or item.IsLocked() or item.GetNetname() != expected["net"]:
            raise RuntimeError(f"Reviewed removal invariant failed for {uid}")
        if expected["kind"] == "segment":
            if isinstance(item, pcbnew.PCB_VIA):
                raise RuntimeError(f"Expected segment removal {uid}")
            actual_ends = tuple(sorted((mm_point(item.GetStart()), mm_point(item.GetEnd()))))
            wanted_ends = tuple(sorted(expected["start_end_mm"]))
            if (
                item.GetLayerName() != expected["layer"]
                or round(pcbnew.ToMM(item.GetWidth()), 9) != expected["width_mm"]
                or actual_ends != wanted_ends
            ):
                raise RuntimeError(f"Reviewed segment invariant failed for {uid}")
        else:
            if not isinstance(item, pcbnew.PCB_VIA):
                raise RuntimeError(f"Expected via removal {uid}")
            actual = (
                mm_point(item.GetPosition()),
                round(pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)), 9),
                round(pcbnew.ToMM(item.GetDrillValue()), 9),
            )
            wanted = (expected["position_mm"], expected["size_mm"], expected["drill_mm"])
            if actual != wanted:
                raise RuntimeError(f"Reviewed via invariant failed for {uid}: {actual}")


def render_addition(entry, net_code: int) -> str:
    if entry["kind"] == "segment":
        start = entry["start_mm"]
        end = entry["end_mm"]
        return (
            f"  (segment (start {format_mm(start[0])} {format_mm(start[1])}) "
            f"(end {format_mm(end[0])} {format_mm(end[1])}) "
            f"(width {format_mm(entry['width_mm'])}) (layer \"{entry['layer']}\") "
            f"(net {net_code}) (tstamp {entry['uuid']}))"
        )
    position = entry["position_mm"]
    return (
        f"  (via (at {format_mm(position[0])} {format_mm(position[1])}) "
        f"(size {format_mm(entry['size_mm'])}) (drill {format_mm(entry['drill_mm'])}) "
        f"(layers \"F.Cu\" \"B.Cu\") (net {net_code}) (tstamp {entry['uuid']}))"
    )


def validate_added(board, net_codes) -> None:
    by_uuid = {item_uuid(item): item for item in board.GetTracks()}
    for expected in ADDITIONS:
        item = by_uuid.get(expected["uuid"])
        if item is None or item.GetNetCode() != net_codes[expected["net"]] or item.IsLocked():
            raise RuntimeError(f"Reload changed added copper {expected['uuid']}")
        if expected["kind"] == "segment":
            if isinstance(item, pcbnew.PCB_VIA):
                raise RuntimeError(f"Expected segment {expected['uuid']}")
            actual = {
                "layer": item.GetLayerName(),
                "start_mm": mm_point(item.GetStart()),
                "end_mm": mm_point(item.GetEnd()),
                "width_mm": round(pcbnew.ToMM(item.GetWidth()), 9),
            }
        else:
            if not isinstance(item, pcbnew.PCB_VIA):
                raise RuntimeError(f"Expected via {expected['uuid']}")
            actual = {
                "position_mm": mm_point(item.GetPosition()),
                "size_mm": round(pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)), 9),
                "drill_mm": round(pcbnew.ToMM(item.GetDrillValue()), 9),
            }
        wanted = {key: expected[key] for key in actual}
        if actual != wanted:
            raise RuntimeError(
                f"Reload changed {expected['uuid']}: expected {wanted}, got {actual}"
            )


def shape_distance(first, second) -> float:
    try:
        collides = first.Collide(second, 0)
    except TypeError:
        collides = second.Collide(first, 0)
    if collides:
        return 0.0
    point_a = pcbnew.VECTOR2I()
    point_b = pcbnew.VECTOR2I()
    if not first.NearestPoints(second, point_a, point_b):
        return math.inf
    return math.hypot(
        pcbnew.ToMM(point_a.x - point_b.x),
        pcbnew.ToMM(point_a.y - point_b.y),
    )


def foreign_copper_clearances(board, target) -> list[dict[str, object]]:
    rows = []
    target_net = target.GetNetCode()
    target_uuid = item_uuid(target)
    layers = list(target.GetLayerSet().Seq())
    for layer in layers:
        target_shape = target.GetEffectiveShape(layer)
        for footprint in board.GetFootprints():
            for pad in footprint.Pads():
                if pad.GetNetCode() == target_net or not pad.IsOnLayer(layer):
                    continue
                rows.append(
                    {
                        "clearance_mm": shape_distance(target_shape, pad.GetEffectiveShape(layer)),
                        "layer": board.GetLayerName(layer),
                        "net": pad.GetNetname(),
                        "kind": f"pad {footprint.GetReference()}.{pad.GetNumber()}",
                        "uuid": item_uuid(pad),
                    }
                )
        for item in board.GetTracks():
            if (
                item_uuid(item) == target_uuid
                or item.GetNetCode() == target_net
                or not item.IsOnLayer(layer)
            ):
                continue
            rows.append(
                {
                    "clearance_mm": shape_distance(target_shape, item.GetEffectiveShape(layer)),
                    "layer": board.GetLayerName(layer),
                    "net": item.GetNetname(),
                    "kind": "via" if isinstance(item, pcbnew.PCB_VIA) else "segment",
                    "uuid": item_uuid(item),
                }
            )
    return sorted(rows, key=lambda row: row["clearance_mm"])


def validate_plane_landing(board, via) -> list[str]:
    position = via.GetPosition()
    layers = sorted(
        {
            board.GetLayerName(layer)
            for zone in board.Zones()
            if zone.GetNetname() == "DGND"
            for layer in zone.GetLayerSet().Seq()
            if zone.HitTestFilledArea(layer, position)
        }
    )
    if not {"In1.Cu", "In4.Cu", "In6.Cu"} <= set(layers):
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
        name: int(board.FindNet(name).GetNetCode()) for name in ("DGND", "HEATER_G1")
    }
    if net_codes != {"DGND": 66, "HEATER_G1": 81}:
        raise RuntimeError(f"Unexpected reviewed net codes: {net_codes}")

    added_uuids = {entry["uuid"] for entry in ADDITIONS}
    if added_uuids & set(before_by_uuid):
        if added_uuids <= set(before_by_uuid):
            raise SystemExit("D27 via-margin upgrade is already installed")
        raise RuntimeError("Only part of the deterministic D27 upgrade is present")

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
        raise RuntimeError("A deterministic D27 upgrade UUID collides with the board")

    insertion = next(
        (index for index, line in enumerate(lines) if line.startswith("  (zone ")), None
    )
    if insertion is None or any(TRACK_LINE.match(line) for line in lines[insertion:]):
        raise RuntimeError("Legacy copper insertion boundary is not as reviewed")
    removal_lines = {copper_lines[uid] for uid in REMOVALS}
    rendered = [
        render_addition(entry, net_codes[entry["net"]]) + newline for entry in ADDITIONS
    ]
    output = [line for index, line in enumerate(lines[:insertion]) if index not in removal_lines]
    output.extend(rendered)
    output.extend(lines[insertion:])
    candidate_bytes = "".join(output).encode("utf-8")

    candidate.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{candidate.stem}.d27-via-margin-",
        suffix=candidate.suffix,
        dir=candidate.parent,
        delete=False,
    ) as temporary:
        temporary.write(candidate_bytes)
        temporary_name = Path(temporary.name)
    os.replace(temporary_name, candidate)

    staged = pcbnew.LoadBoard(str(candidate))
    after = inventory(staged)
    removed_segments = sum(entry["kind"] == "segment" for entry in REMOVALS.values())
    removed_vias = sum(entry["kind"] == "via" for entry in REMOVALS.values())
    added_segments = sum(entry["kind"] == "segment" for entry in ADDITIONS)
    added_vias = sum(entry["kind"] == "via" for entry in ADDITIONS)
    expected_after = dict(before)
    expected_after["segments"] = before["segments"] - removed_segments + added_segments
    expected_after["vias"] = before["vias"] - removed_vias + added_vias
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
    validate_added(staged, net_codes)

    pcbnew.ZONE_FILLER(staged).Fill(staged.Zones())
    for name, pad_uuids in PAD_GROUPS.items():
        if not group_connected(staged, pad_uuids):
            raise RuntimeError(f"D27 upgrade disconnected {name}")
    via = after_by_uuid["11d82c0e-fa6b-56b7-ba61-79a3d4f3623e"]
    segment = after_by_uuid["744e5601-cda5-5f4a-8554-33b7cfdfc230"]
    plane_layers = validate_plane_landing(staged, via)
    d27_pad = find_item(staged, D27_PAD_UUID)
    connected_d27 = {
        item_uuid(item)
        for item in staged.GetConnectivity().GetConnectedItems(d27_pad)
        if isinstance(item, (pcbnew.PAD, pcbnew.PCB_TRACK))
    }
    if not {item_uuid(segment), item_uuid(via)} <= connected_d27:
        raise RuntimeError("Upgraded D27 return is not natively connected to D27.1")

    via_clearances = foreign_copper_clearances(staged, via)
    segment_clearances = foreign_copper_clearances(staged, segment)
    if via_clearances[0]["clearance_mm"] < 0.309:
        raise RuntimeError(f"D27 via clearance regressed: {via_clearances[0]}")
    if segment_clearances[0]["clearance_mm"] < 0.431:
        raise RuntimeError(f"D27 return clearance regressed: {segment_clearances[0]}")

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
            "pcbnew validated native objects, pad connectivity, DGND plane overlap, and "
            "native-shape copper clearances; only reviewed legacy copper records changed"
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
        "added": ADDITIONS,
        "via_dgnd_plane_layers": plane_layers,
        "geometry": {
            "previous_via": {
                "position_mm": [78.65, 127.4],
                "size_drill_mm": [0.6, 0.3],
                "annular_ring_mm": 0.15,
                "nominal_aspect_ratio_at_1_6_mm": 5.333333,
                "minimum_routed_copper_clearance_mm": 0.250002,
            },
            "installed_via": {
                "position_mm": [78.735, 127.575],
                "size_drill_mm": [0.65, 0.3],
                "annular_ring_mm": 0.175,
                "nominal_aspect_ratio_at_1_6_mm": 5.333333,
                "minimum_routed_copper_clearance": via_clearances[0],
                "next_routed_copper_clearances": via_clearances[1:4],
            },
            "installed_return": {
                "width_mm": 0.6,
                "minimum_routed_copper_clearance": segment_clearances[0],
            },
        },
        "fabrication_basis": {
            "fabricator": "JLCPCB",
            "capability_urls": {
                "rigid_pcb": "https://jlcpcb.com/capabilities/Capab",
                "via_aspect_ratio": (
                    "https://jlcpcb.com/blog/via-aspect-ratio-critical-pcb-reliability"
                ),
            },
            "published_via_guidance": (
                "0.30 mm and larger drill is a standard process; via diameter should be at "
                "least 0.10 mm larger than the hole and 0.15 mm larger is preferred"
            ),
            "design_pad_minus_hole_mm": 0.35,
            "trade_study": (
                "the preferred 0.80/0.40 mm class via required three signal reroutes and "
                "remained pinched near 0.284 mm; 0.65/0.30 mm provides 0.310 mm minimum "
                "routed-copper clearance with only the HEATER_G1 reroute"
            ),
            "disposition": (
                "the D27 via-specific zero-margin hold is closed at layout level; final "
                "stackup/fabricator review and D27 transient/component qualification remain"
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
                "via_min_clearance_mm": round(via_clearances[0]["clearance_mm"], 9),
                "segment_min_clearance_mm": round(
                    segment_clearances[0]["clearance_mm"], 9
                ),
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
        prefix=f".{BOARD.stem}.d27-via-margin-",
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
