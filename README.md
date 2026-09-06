# zai-disclosure-ledger

Archive of the **Z.ai Security Disclosure Ledger** (披露账本) — the coordinated
vulnerability disclosure record for vulnerabilities found using GLM models,
published at `cvd.z.ai`. Z.ai removed the public detail pages after this
capture; this repo preserves the last public snapshot for personal reference.

**Source**: Wayback Machine capture of `https://cvd.z.ai/ledger/`,
`2026-08-14` → <https://web.archive.org/web/20260814211237/https://cvd.z.ai/ledger/>

## Contents

| Path | What it is |
|---|---|
| `raw/ledger-20260814.html` | Verbatim archived HTML (2 MB). The full dataset is embedded in the page's Next.js RSC payload (`self.__next_f` script chunks) — the site paginated client-side over the complete dataset, so one page holds everything. |
| `data/vulnerabilities.json` | Canonical extraction: 2,436 entries, full fidelity, nulls preserved. |
| `data/vulnerabilities.csv` | Flattened view (arrays joined with `;`, nulls empty). |
| `STATS.md` | Generated rollups: severity, status, year, projects, researchers, disclosure coverage. |
| `scripts/fetch.sh` | Re-downloads the archived page. |
| `scripts/parse.py` | Extracts the RSC payload → `data/` + `STATS.md`. |

## Regenerate

```sh
scripts/fetch.sh          # refresh raw/ from the Wayback Machine
python3 scripts/parse.py  # rebuild data/ and STATS.md
```

## Field schema (`data/vulnerabilities.json` entries)

| Field | Type | Notes |
|---|---|---|
| `id` | uuid | site-internal id |
| `internalId` | string | public finding ID, `ZAI-YYYY-XXXXXX` |
| `isPublic` | bool | only 53 of 2,436 were publicly disclosed at capture time |
| `targetProject` / `targetProjectDisplay` | string | affected open-source project |
| `severity` | enum | critical / high / medium / low |
| `discoveredAt` | date | |
| `introducedYear` | int | year the vulnerability was introduced |
| `language` | string | base language of the entry |
| `status` | enum | discovered / reported / sent_to_maintainer / acknowledged / patched / revealed |
| `researcher` | `{name, url}` | e.g. 南开大学AOSP实验室 (Nankai University AOSP Lab) |
| `harness` | string/null | |
| `commitHash` | string | hash referencing the vulnerable code state |
| `translations` | array | bilingual versions: `{lang, title, report, autoTranslated}` — 中文 + English |
| `title` / `report` | string/null | disclosure text (null unless `isPublic`) |
| `revealedAt` | date/null | |
| `cveIds` / `ghsaIds` / `cnvdIds` | array/null | assigned identifiers |
| `createdAt` / `updatedAt` | date/null | |

## Caveats

- This is a **single snapshot** from a third-party capture (Wayback Machine),
  not an official export. The backing `/api/v1/index` API and any per-finding
  detail pages were not archived; the embedded client-side dataset is the only
  surviving source.
- 2,383 of 2,436 findings were **not publicly disclosed** at capture time —
  their `title`, `report`, and identifier fields are `null`. That null-ness is
  part of the historical record and is preserved as-is.
- `translations` marked `autoTranslated: true` are machine-translated text.
- Capture taken 2026-08-14 (site timestamp); extracted into git 2026-09-06.

## License / use

The extraction scripts (`scripts/`) are licensed under the **GNU GPL v3**
(see `LICENSE`). The archived data (`raw/`, `data/vulnerabilities.json`,
`data/vulnerabilities.csv`) is **not** covered by that license — it
originates from Z.ai's public disclosure ledger, and individual findings
remain subject to their own disclosure terms. This repo is a personal
reference archive.
