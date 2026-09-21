"""Generate a read-only, reproducible static baseline for the R10 board.

This intentionally does not replace KiCad DRC/ERC. It inventories the native
files without importing pcbnew so the stale-report delta and release holds are
visible even on machines that do not have KiCad installed.
"""

from __future__ import annotations

import collections
import csv
import hashlib
import io
import json
import math
import re
import subprocess
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "GrandMarquis97_RevA.kicad_pcb"
PROJECT = ROOT / "GrandMarquis97_RevA.kicad_pro"
DRC = ROOT / "reports" / "After_routing_DRC.txt"
SAVED_VALIDATION = ROOT / "reports" / "Routing_validation.json"
OUTPUT = ROOT / "production_review"


def git(*arguments: str, binary: bool = False):
    return subprocess.check_output(
        ["git", *arguments], cwd=ROOT, text=not binary
    )


def baseline_commit() -> str:
    try:
        return git("merge-base", "HEAD", "origin/main").strip()
    except subprocess.CalledProcessError:
        return git("rev-parse", "HEAD").strip()


def number(pattern: str, text: str, default: float | None = None) -> float | None:
    match = re.search(pattern, text)
    return float(match.group(1)) if match else default


def extract_blocks(text: str, prefix: str) -> list[str]:
    """Return balanced top-level blocks beginning with ``prefix``."""
    blocks: list[str] = []
    start = 0
    while True:
        start = text.find(prefix, start)
        if start < 0:
            return blocks
        depth = 0
        quoted = False
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if escaped:
                escaped = False
                continue
            if quoted and char == "\\":
                escaped = True
            elif char == '"':
                quoted = not quoted
            elif not quoted:
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        blocks.append(text[start : index + 1])
                        start = index + 1
                        break
        else:
            raise ValueError(f"Unbalanced block beginning at byte {start}: {prefix}")


def rounded(value: str) -> float:
    return round(float(value), 9)


def segment_record(line: str, net_names: dict[int, str]) -> dict[str, object]:
    points = re.findall(r"\((?:start|end) ([\d.+-]+) ([\d.+-]+)\)", line)
    if len(points) != 2:
        raise ValueError(f"Could not parse segment: {line}")
    (x1, y1), (x2, y2) = [(rounded(x), rounded(y)) for x, y in points]
    net = int(re.search(r"\(net (\d+)\)", line).group(1))
    return {
        "start": (x1, y1),
        "end": (x2, y2),
        "width_mm": rounded(re.search(r"\(width ([\d.+-]+)\)", line).group(1)),
        "layer": re.search(r'\(layer "([^"]+)"\)', line).group(1),
        "net_code": net,
        "net": net_names.get(net, f"<net {net}>") if net else "",
        "locked": line.startswith("  (segment locked "),
    }


def via_record(line: str, net_names: dict[int, str]) -> dict[str, object]:
    at = re.search(r"\(at ([\d.+-]+) ([\d.+-]+)\)", line)
    layers = re.search(r'\(layers "([^"]+)" "([^"]+)"\)', line)
    net = int(re.search(r"\(net (\d+)\)", line).group(1))
    return {
        "at": (rounded(at.group(1)), rounded(at.group(2))),
        "size_mm": rounded(re.search(r"\(size ([\d.+-]+)\)", line).group(1)),
        "drill_mm": rounded(re.search(r"\(drill ([\d.+-]+)\)", line).group(1)),
        "layers": (layers.group(1), layers.group(2)),
        "net_code": net,
        "net": net_names.get(net, f"<net {net}>") if net else "",
        "locked": line.startswith("  (via locked "),
    }


def duplicate_summary(items: list[dict[str, object]], key) -> tuple[int, int]:
    counts = collections.Counter(key(item) for item in items)
    groups = sum(count > 1 for count in counts.values())
    extras = sum(count - 1 for count in counts.values() if count > 1)
    return groups, extras


def board_mapping(board_text: str) -> tuple[int, int, list[dict[str, str]]]:
    actual: dict[tuple[str, str], str] = {}
    pad_count = 0
    for block in extract_blocks(board_text, "  (footprint "):
        reference = re.search(r'\(fp_text reference "([^"]+)"', block)
        if not reference:
            continue
        ref = reference.group(1)
        for pad in extract_blocks(block, "    (pad "):
            pad_count += 1
            pin = re.match(r'    \(pad "([^"]*)"', pad).group(1)
            net = re.search(r'\(net \d+ "([^"]*)"\)', pad)
            if net and net.group(1):
                actual[ref, pin] = net.group(1)

    expected: dict[tuple[str, str], str] = {}
    root = ET.parse(ROOT / "source" / "input_netlist.xml").getroot()
    for net in root.find("nets"):
        if net.attrib["name"].startswith("unconnected"):
            continue
        for node in net.findall("node"):
            if node.attrib["ref"] != "J121":
                expected[node.attrib["ref"], node.attrib["pin"]] = net.attrib["name"]

    differences: list[dict[str, str]] = []
    for key in sorted(expected.keys() | actual.keys()):
        if expected.get(key) != actual.get(key):
            differences.append(
                {
                    "reference": key[0],
                    "pad": key[1],
                    "expected": expected.get(key, "<absent>"),
                    "actual": actual.get(key, "<absent>"),
                }
            )
    return pad_count, len(expected), differences


def histogram(lengths: list[float]) -> dict[str, int]:
    buckets = [
        ("zero", lambda value: value == 0),
        (">0-0.05", lambda value: 0 < value <= 0.05),
        (">0.05-0.10", lambda value: 0.05 < value <= 0.10),
        (">0.10-0.25", lambda value: 0.10 < value <= 0.25),
        (">0.25-1.00", lambda value: 0.25 < value <= 1.00),
        (">1.00", lambda value: value > 1.00),
    ]
    return {name: sum(test(value) for value in lengths) for name, test in buckets}


def tracked_hashes(commit: str) -> list[tuple[str, str]]:
    archive = git("archive", "--format=tar", commit, binary=True)
    rows = []
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as files:
        for member in files.getmembers():
            if member.isfile():
                content = files.extractfile(member).read()
                rows.append((hashlib.sha256(content).hexdigest(), member.name))
    return sorted(rows, key=lambda row: row[1])


def main() -> None:
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT / "baseline").mkdir(exist_ok=True)
    board_text = BOARD.read_text(encoding="utf-8")
    project = json.loads(PROJECT.read_text(encoding="utf-8"))
    saved = json.loads(SAVED_VALIDATION.read_text(encoding="utf-8"))
    baseline = baseline_commit()

    net_names = {
        int(code): name
        for code, name in re.findall(r'^  \(net (\d+) "([^"]*)"\)$', board_text, re.M)
    }
    segment_lines = re.findall(r"^  \(segment .+$", board_text, re.M)
    via_lines = re.findall(r"^  \(via .+$", board_text, re.M)
    segments = [segment_record(line, net_names) for line in segment_lines]
    vias = [via_record(line, net_names) for line in via_lines]
    lengths = [math.dist(item["start"], item["end"]) for item in segments]

    segment_groups, segment_extras = duplicate_summary(
        segments,
        lambda item: (
            tuple(sorted((item["start"], item["end"]))),
            item["width_mm"],
            item["layer"],
            item["net_code"],
        ),
    )
    via_groups, via_extras = duplicate_summary(
        vias,
        lambda item: (
            item["at"],
            item["size_mm"],
            item["drill_mm"],
            item["layers"],
            item["net_code"],
        ),
    )

    zone_blocks = extract_blocks(board_text, "  (zone ")
    zones = []
    for block in zone_blocks:
        name = re.search(r'\(net_name "([^"]*)"\)', block)
        layer = re.search(r'\(layer "([^"]+)"\)', block)
        layers = re.search(r'\(layers ([^)]+)\)', block)
        zones.append(
            {
                "net": name.group(1) if name else "",
                "layers": [layer.group(1)] if layer else re.findall(r'"([^"]+)"', layers.group(1)) if layers else [],
                "rule_area_or_keepout": "(keepout" in block,
            }
        )

    pad_count, expected_pairs, mapping_differences = board_mapping(board_text)
    drc_text = DRC.read_text(encoding="utf-8")
    drc_counts = dict(collections.Counter(re.findall(r"^\[([^]]+)\]", drc_text, re.M)))
    drc_created = re.search(r"\*\* Created on (.+?) \*\*", drc_text)
    design = project["board"]["design_settings"]
    ignored = sorted(
        name for name, severity in design["rule_severities"].items() if severity == "ignore"
    )
    net_settings = project["net_settings"]

    locked_rows = []
    locked_counts: collections.Counter[tuple[str, str, str]] = collections.Counter()
    for item in segments:
        if item["locked"]:
            locked_counts[(str(item["net"]), str(item["layer"]), "segment")] += 1
    for item in vias:
        if item["locked"]:
            locked_counts[(str(item["net"]), " -> ".join(item["layers"]), "via")] += 1
    for (net, layer, kind), count in sorted(locked_counts.items()):
        locked_rows.append({"net": net, "layer_or_span": layer, "object_type": kind, "count": count})

    audit = {
        "scope": "static native-file audit; does not replace KiCad DRC/ERC",
        "baseline_commit": baseline,
        "audited_git_head": git("rev-parse", "HEAD").strip(),
        "audited_files_from_worktree": True,
        "kicad_runtime": "NOT AVAILABLE in audit environment",
        "board_file_version": int(re.search(r"\(kicad_pcb \(version (\d+)\)", board_text).group(1)),
        "board_thickness_mm": number(r"\(thickness ([\d.]+)\)", board_text),
        "copper_layers": [name for _, name in re.findall(r'^    \((\d+) "([^"]+)" signal\)$', board_text, re.M)],
        "physical_stackup_embedded": "(stackup" in board_text,
        "counts": {
            "footprints": len(re.findall(r"^  \(footprint ", board_text, re.M)),
            "pads": pad_count,
            "named_nets": sum(bool(name) for name in net_names.values()),
            "segments": len(segments),
            "vias": len(vias),
            "zones_total": len(zones),
            "copper_zones": sum(not zone["rule_area_or_keepout"] for zone in zones),
            "rule_areas_or_keepouts": sum(zone["rule_area_or_keepout"] for zone in zones),
            "locked_segments": sum(item["locked"] for item in segments),
            "locked_vias": sum(item["locked"] for item in vias),
            "zero_length_segments": sum(length == 0 for length in lengths),
            "exact_duplicate_segment_groups": segment_groups,
            "extra_duplicate_segment_records": segment_extras,
            "exact_duplicate_via_groups": via_groups,
            "extra_duplicate_via_records": via_extras,
        },
        "segment_length_histogram_mm": histogram(lengths),
        "track_width_counts": {
            f"{width:g}": count
            for width, count in sorted(collections.Counter(item["width_mm"] for item in segments).items())
        },
        "via_size_drill_span_counts": {
            f"{size:g}/{drill:g} mm, {start}->{end}": count
            for (size, drill, (start, end)), count in sorted(
                collections.Counter((item["size_mm"], item["drill_mm"], item["layers"]) for item in vias).items()
            )
        },
        "zones": zones,
        "rule_severities_ignored": ignored,
        "drc_exclusions": design["drc_exclusions"],
        "project_minimums": design["rules"],
        "net_classes": net_settings["classes"],
        "net_class_patterns": net_settings["netclass_patterns"],
        "schematic_netlist_mapping": {
            "expected_assigned_pairs_excluding_J121": expected_pairs,
            "matches": not mapping_differences,
            "differences": mapping_differences,
        },
        "saved_drc": {
            "created": drc_created.group(1) if drc_created else "unknown",
            "counts": drc_counts,
            "fresh_native_run": False,
        },
        "stale_validation_delta": {
            "segments": len(segments) - saved["tracks"],
            "vias": len(vias) - saved["vias"],
        },
        "release_state": "ROUTING_INCOMPLETE",
    }
    (OUTPUT / "BASELINE_AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")

    with (OUTPUT / "LOCKED_COPPER_AUDIT.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["net", "layer_or_span", "object_type", "count"])
        writer.writeheader()
        writer.writerows(locked_rows)

    hashes = tracked_hashes(baseline)
    (OUTPUT / "baseline" / "SHA256SUMS.txt").write_text(
        "".join(f"{digest}  {name}\n" for digest, name in hashes), encoding="utf-8"
    )

    counts = audit["counts"]
    markdown = f"""# R10 static baseline audit

This report inventories the current working-tree native files without modifying the board. The preserved baseline is commit `{audit['baseline_commit']}`. This audit supplements, but does not replace, native KiCad DRC/ERC. KiCad was not available in the audit environment, so the checked-in DRC remains stale and release-blocking.

## Native-file inventory

- Board format version: `{audit['board_file_version']}`
- Board thickness: {audit['board_thickness_mm']:.2f} mm
- Copper layers: {', '.join(audit['copper_layers'])}
- Embedded physical stackup: **no**
- Footprints / pads / named nets: {counts['footprints']} / {counts['pads']} / {counts['named_nets']}
- Segments / vias / zones: {counts['segments']} / {counts['vias']} / {counts['zones_total']}
- Locked segments / vias: {counts['locked_segments']} / {counts['locked_vias']}
- Zero-length segments: {counts['zero_length_segments']}
- Exact duplicate segment groups / extra records: {counts['exact_duplicate_segment_groups']} / {counts['extra_duplicate_segment_records']}
- Exact duplicate via groups / extra records: {counts['exact_duplicate_via_groups']} / {counts['extra_duplicate_via_records']}
- Stored-netlist comparison: {expected_pairs} assigned pairs, {'MATCH' if not mapping_differences else 'MISMATCH'}

## Stale checked-in evidence

`reports/Routing_validation.json` understates the native board by **{audit['stale_validation_delta']['segments']} segments** and **{audit['stale_validation_delta']['vias']} vias**. The saved DRC was created on {audit['saved_drc']['created']} and was not rerun for this audit.

Saved DRC categories: `{json.dumps(drc_counts, sort_keys=True)}`

## Rule concerns

- Project minimum track width: {design['rules']['min_track_width']} mm
- Project minimum clearance: {design['rules']['min_clearance']} mm
- Globally ignored categories: {', '.join(ignored)}
- DRC exclusions: {len(design['drc_exclusions'])}
- The Default class remains 0.20 mm and there is no assigned 0.25 mm Signal class.

## Release disposition

`ROUTING_INCOMPLETE`

Do not modify routing or release fabrication outputs from this static audit. A fresh native DRC and ERC, zone refill, visual review, and all documented electrical/mechanical qualification gates remain required.
"""
    (OUTPUT / "BASELINE_AUDIT.md").write_text(markdown, encoding="utf-8")

    locked_md = f"""# Locked copper audit summary

The native board contains **{counts['locked_segments']} locked segments** and **{counts['locked_vias']} locked vias**. `LOCKED_COPPER_AUDIT.csv` groups them by net and layer/span. This is an inventory only: route purpose and justification still require engineering review before any lock is removed.
"""
    (OUTPUT / "LOCKED_COPPER_AUDIT.md").write_text(locked_md, encoding="utf-8")
    print(json.dumps({"counts": counts, "mapping_differences": len(mapping_differences)}, indent=2))


if __name__ == "__main__":
    main()
