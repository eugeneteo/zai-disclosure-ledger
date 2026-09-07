#!/usr/bin/env python3
"""Parse the archived Z.ai CVD ledger HTML (Next.js RSC payload) into data/.

SPDX-License-Identifier: GPL-3.0-only
This file is part of zai-disclosure-ledger
<https://github.com/eugeneteo/zai-disclosure-ledger>, licensed under the
GNU General Public License v3.0. See the LICENSE file at the repo root or
<https://www.gnu.org/licenses/gpl-3.0.html>.

Usage: scripts/parse.py [raw/ledger-20260814.html]
"""
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HTML_PATH = sys.argv[1] if len(sys.argv) > 1 else REPO / "raw/ledger-20260814.html"

FIELD_ORDER = [
    "id", "internalId", "isPublic", "targetProject", "targetProjectDisplay",
    "severity", "discoveredAt", "introducedYear", "language", "status",
    "researcher", "harness", "commitHash", "translations", "title", "report",
    "revealedAt", "cveIds", "ghsaIds", "cnvdIds", "createdAt", "updatedAt",
]


def js_unescape(s: str) -> str:
    """Decode a JS double-quoted string body (as embedded in HTML)."""
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            if n == "u" and i + 5 < len(s):
                out.append(chr(int(s[i + 2:i + 6], 16)))
                i += 6
                continue
            mapping = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f",
                       '"': '"', "\\": "\\", "/": "/", "'": "'"}
            out.append(mapping.get(n, n))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def extract_flight(html: str) -> str:
    """Concatenate the RSC flight payload from self.__next_f.push([1,"..."]) calls."""
    chunks = []
    # script bodies
    for body in re.findall(r"<script[^>]*>(.*?)</script>", html, re.S):
        if "self.__next_f" not in body:
            continue
        for m in re.finditer(r'self\.__next_f\.push\(\s*\[\s*1\s*,\s*"((?:[^"\\]|\\.)*)"\s*\]', body, re.S):
            chunks.append(js_unescape(m.group(1)))
    return "".join(chunks)


def extract_entries(flight: str) -> list:
    """Scan the flight payload for balanced JSON objects containing internalId."""
    entries = {}
    for m in re.finditer(r'\{"id":"', flight):
        start = m.start()
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(flight)):
            c = flight[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    obj_text = flight[start:i + 1]
                    try:
                        obj = json.loads(obj_text)
                    except json.JSONDecodeError:
                        break
                    if isinstance(obj, dict) and "internalId" in obj:
                        entries[obj["internalId"]] = obj
                    break
    return list(entries.values())


def flatten(entry: dict) -> dict:
    row = {}
    for k in FIELD_ORDER:
        v = entry.get(k)
        if k == "researcher" and isinstance(v, dict):
            v = v.get("name")
        elif isinstance(v, list):
            v = ";".join(str(x) for x in v)
        elif isinstance(v, (dict, bool)):
            v = json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else ("true" if v else "false")
        row[k] = "" if v is None else v
    return row


def write_stats(entries: list, path: Path):
    def count(key):
        return Counter(e.get(key) if e.get(key) is not None else "(none)" for e in entries)

    total = len(entries)
    public = sum(1 for e in entries if e.get("isPublic"))
    titled = sum(1 for e in entries if e.get("title"))
    reported = sum(1 for e in entries if e.get("report"))
    translated = sum(1 for e in entries if e.get("translations"))
    with_cve = sum(1 for e in entries if e.get("cveIds"))
    with_ghsa = sum(1 for e in entries if e.get("ghsaIds"))
    with_cnvd = sum(1 for e in entries if e.get("cnvdIds"))
    years = Counter(e.get("discoveredAt", "")[:4] for e in entries if e.get("discoveredAt"))

    def table(counter, header):
        pairs = counter.most_common() if isinstance(counter, Counter) else counter
        lines = [f"| {header} | Count |", "|---|---:|"]
        for k, v in pairs:
            lines.append(f"| {k} | {v} |")
        return "\n".join(lines)

    proj = Counter(e.get("targetProjectDisplay", "(unknown)") for e in entries)
    md = f"""# Z.ai CVD Disclosure Ledger — Statistics

Snapshot of {total} findings from the archived ledger (Wayback capture 2026-08-14).
Regenerate with `scripts/parse.py`.

## Overview

| Metric | Count |
|---|---:|
| Total findings | {total} |
| Publicly disclosed (`isPublic`) | {public} |
| Undisclosed | {total - public} |
| With title | {titled} |
| With report | {reported} |
| With translations (bilingual) | {translated} |
| With CVE IDs | {with_cve} |
| With GHSA IDs | {with_ghsa} |
| With CNVD IDs | {with_cnvd} |

## By severity

{table(count("severity"), "Severity")}

## By status

{table(count("status"), "Status")}

## By discovery year

{table(years, "Year")}

## Top 25 affected projects

{table(proj.most_common(25), "Project")}

## By researcher

{table(Counter((e.get("researcher") or {}).get("name", "(unknown)") for e in entries), "Researcher")}
"""
    path.write_text(md, encoding="utf-8")


def main():
    html = HTML_PATH.read_bytes().decode("utf-8", errors="replace")
    flight = extract_flight(html)
    entries = extract_entries(flight)
    ids = {e["internalId"] for e in entries}
    print(f"flight payload: {len(flight):,} chars; entries: {len(entries):,}; unique ids: {len(ids):,}")
    assert len(ids) >= 2436, f"expected >=2436 unique internalIds, got {len(ids)}"
    # sanity: Chinese text round-trips
    sample = next(e for e in entries if e["internalId"] == "ZAI-2026-WG3PIQ")
    assert "南开大学" in (sample.get("researcher") or {}).get("name", ""), \
        f"Chinese mojibake: {sample.get('researcher')}"

    (REPO / "data").mkdir(exist_ok=True)
    source = "https://web.archive.org/web/20260814211237/https://cvd.z.ai/ledger/"
    # capturedAt is derived from the Wayback timestamp embedded in the source
    # URL so re-parsing is byte-reproducible (it is the capture time, not the
    # parse time; datetime.now() here would dirty the tree on every re-run).
    m = re.search(r"/web/(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/", source)
    captured_at = (f"{m.group(1)}-{m.group(2)}-{m.group(3)}T"
                   f"{m.group(4)}:{m.group(5)}:{m.group(6)}+00:00")
    doc = {
        "source": source,
        "capturedAt": captured_at,
        "siteCapture": "2026-08-14",
        "entryCount": len(entries),
        "entries": entries,
    }
    (REPO / "data/vulnerabilities.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    with open(REPO / "data/vulnerabilities.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELD_ORDER)
        w.writeheader()
        for e in entries:
            w.writerow(flatten(e))

    write_stats(entries, REPO / "STATS.md")
    print("wrote data/vulnerabilities.json, data/vulnerabilities.csv, STATS.md")


if __name__ == "__main__":
    main()
