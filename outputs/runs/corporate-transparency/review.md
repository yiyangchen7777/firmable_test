# Mapping review — corporate-transparency

| | |
|---|---|
| Dataset | corporate-transparency — Corporate Tax Transparency |
| Publisher / licence | Australian Taxation Office / cc-by |
| Resource | https://data.gov.au/data/dataset/c2524c87-cea4-4636-acac-599a82048a26/resource/15bf4eaa-7a14-48e9-8a3f-092df32a644e/download/2024-25-corporate-report-of-entity-tax-information.xlsx |
| Reader | {"format": "xlsx", "delimiter": null, "encoding": "utf-8", "header_row": 0, "sheet": "Income tax details"} |
| Agent run | revisions used 1/3 · steps 8 |
| **Status** | **PASSING** |
| Source reliability | 0.9 — The ATO is the national tax regulator publishing its own corporate tax transparency report under CC-BY, so names and ABNs are authoritative. |
| Record id | column ['Name', 'Income year'] — The report has no record key and the ABN is nullable (1.5% blank, 197 distinct over 200 rows), so ABN alone is not unique. The Name column is 100% populated with 200 distinct values across 200 rows. Each entity appears once per income year, and the sample covers a single year, so Name is unique per record. |
| Observed at | dataset_modified → 2026-10-12 (basis: proxy) — There is no per-record extract or update date column. 'Income year' is a reporting period label, not an assertion date, so I use the catalogue modified date as a weak proxy. |

## Mapping (2 field mappings from 6 source columns)

| canonical | ← source column | transforms | conf. | cond. | evidence |
|---|---|---|---|---|---|
| entity.legal_name | Name | `["trim", "empty_to_null"]` | 0.9 |  | Column 'Name' holds values like 'ALLIANZ AUSTRALIA LIMITED' and 'B & E FOODS PTY LTD'. These are registered corporate names with suffixes such as PTY LTD, not trading names. The report is of tax entities identified by na |
| entity.abn | ABN | `["trim", "empty_to_null", "strip_float_suffix", "abn_normalize"]` | 0.95 |  | Column 'ABN' has values like '23068447763' and '21000006226'. All are 11 digits (profile hint), and the ATO describes the report as containing each entity's ABN. It is not an ACN because the values are 11 digits. About 1 |

## Validation — 350 held-out rows (loop set; final acceptance runs once after approval)

| check | threshold | result | pass |
|---|---|---|---|
| identifier checksum (entity.abn) | >= 95% | 100.0% (350 ok / 0 failed) | ✅ |
| null drift (entity.legal_name ← Name) | <= +2pp | +0.0% | ✅ |
| null drift (entity.abn ← ABN) | <= +2pp | +0.0% | ✅ |
| record_id effectively unique (full sample) | <= 0.5% duplicates | 0 duplicates (0.00%) | ✅ |
| minimum useful (a name or an identifier mapped) | required | yes | ✅ |

### Failing examples
none

## Semantic spot-check — 10 held-out records: 20 ok, 0 suspicious

| record | field | verdict | why |
|---|---|---|---|
| AUSPORK LIMITED|2024-25 | entity.legal_name | ok | The 'Name' column is the tax-entity name and 'AUSPORK LIMITED' carries a corporate suffix, so it is the registered name. |
| AUSPORK LIMITED|2024-25 | entity.abn | ok | The ABN belongs to the row's entity and the 11-digit value passes the ABN checksum. |
| BEST FAB PTY LTD|2024-25 | entity.legal_name | ok | 'BEST FAB PTY LTD' is a registered-style company name from the entity Name column. |
| BEST FAB PTY LTD|2024-25 | entity.abn | ok | The ABN is the row's own identifier and passes the checksum. |
| BENDIGO AND ADELAIDE BANK LIMITED|2024-25 | entity.legal_name | ok | This is the full registered bank name, not a brand or trading name. |
| BENDIGO AND ADELAIDE BANK LIMITED|2024-25 | entity.abn | ok | The ABN passes the checksum and is the entity's own, with no agent or parent column on the row. |
| AVENG AUSTRALIA HOLDINGS PTY LTD|2024-25 | entity.legal_name | ok | The name is the reported entity itself. 'Holdings' is part of the registered name, and the row has no separate parent column. |
| AVENG AUSTRALIA HOLDINGS PTY LTD|2024-25 | entity.abn | ok | The ABN passes the checksum and sits on the same row as its entity name. |
| APS GROUP (HOLDINGS) PTY LTD|2024-25 | entity.legal_name | ok | The parentheses are part of the registered name and it is copied verbatim from the entity Name column. |
| APS GROUP (HOLDINGS) PTY LTD|2024-25 | entity.abn | ok | The ABN passes the checksum and belongs to the row's entity. |
| BARALABA COAL COMPANY PTY LTD|2024-25 | entity.legal_name | ok | 'BARALABA COAL COMPANY PTY LTD' is a corporate registered name. |
| BARALABA COAL COMPANY PTY LTD|2024-25 | entity.abn | ok | The ABN passes the checksum and is the row entity's own. |
| BNC GLOBAL INVESTMENTS PTY LTD|2024-25 | entity.legal_name | ok | The Name column holds a corporate name with a PTY LTD suffix. |
| BNC GLOBAL INVESTMENTS PTY LTD|2024-25 | entity.abn | ok | The ABN passes the checksum and matches the row's entity. |
| AMENTUM AUSTRALIA PROPRIETARY LIMITED|2024-25 | entity.legal_name | ok | 'PROPRIETARY LIMITED' is the long-form company suffix, so this is the registered name. |
| AMENTUM AUSTRALIA PROPRIETARY LIMITED|2024-25 | entity.abn | ok | The ABN passes the checksum and belongs to the row's entity. |
| ARCHIES FOOTWEAR PTY LTD|2024-25 | entity.legal_name | ok | The name carries a PTY LTD suffix, so it is the registered name even though it resembles a brand. |
| ARCHIES FOOTWEAR PTY LTD|2024-25 | entity.abn | ok | The ABN passes the checksum and is the row entity's own. |
| BGC (AUSTRALIA) PTY LTD|2024-25 | entity.legal_name | ok | This is a registered company name copied verbatim from the entity Name column. |
| BGC (AUSTRALIA) PTY LTD|2024-25 | entity.abn | ok | The ABN passes the checksum and belongs to the row's entity. |

Notes: All 10 ABNs pass the mod-89 checksum, and every Name value is a corporate name with a company suffix.; The unmapped columns (Total income, Taxable income, Tax payable, Income year) are financial or period data. None was wrongly mapped to a date or status field, and they create no party or identifier ambiguity.; The source is an ATO tax-transparency style report with one entity per row. It carries no separate agent, parent or trading-name columns that could confuse legal_name or abn.

## Unmapped columns (4)

| source column | reason |
|---|---|
| Total income $ | Financial aggregate statistic (e.g. 103673135) for the income year, not an entity attribute in the ontology. |
| Taxable income $ | Financial aggregate statistic (e.g. 5784882), not an entity attribute in the ontology; also about 20% blank. |
| Tax payable $ | Financial aggregate statistic (e.g. 1735465), not an entity attribute in the ontology. |
| Income year | Reporting period label ('2024-25') rather than a date. It is not a registration date or a per-record extract date, and no ontology field fits. |

## Side-by-side — 5 raw records vs their canonical observations

Read these for meaning, not parse success: is the date a registration date or a
licence date? Is the name the licensee or the applicant? Is the ABN the subject
entity's?

### Example 1 — source_record_id AUSTRALIAN POSTAL CORPORATION|2024-25
RAW
```
Name: AUSTRALIAN POSTAL CORPORATION
ABN: 28864970579
Total income $: 9714900825
Taxable income $: 67626224
Tax payable $: 19457009
Income year: 2024-25
```
CANONICAL
```
entity.legal_name = "AUSTRALIAN POSTAL CORPORATION"    (raw: "AUSTRALIAN POSTAL CORPORATION", field_confidence: 0.9)
entity.abn = "28864970579"    (raw: "28864970579", field_confidence: 0.95)
```

### Example 2 — source_record_id AUSTRALIAN LOGISTICS ACQUISITION HOLDINGS PTY LTD|2024-25
RAW
```
Name: AUSTRALIAN LOGISTICS ACQUISITION HOLDINGS PTY LTD
ABN: 28611628909
Total income $: 2318405446
Taxable income $: 
Tax payable $: 
Income year: 2024-25
```
CANONICAL
```
entity.legal_name = "AUSTRALIAN LOGISTICS ACQUISITION HOLDINGS PTY LTD"    (raw: "AUSTRALIAN LOGISTICS ACQUISITION HOLDING", field_confidence: 0.9)
entity.abn = "28611628909"    (raw: "28611628909", field_confidence: 0.95)
```

### Example 3 — source_record_id ALCON LABORATORIES (AUSTRALIA) PTY LTD|2024-25
RAW
```
Name: ALCON LABORATORIES (AUSTRALIA) PTY LTD
ABN: 88000740830
Total income $: 347900229
Taxable income $: 7591333
Tax payable $: 2277400
Income year: 2024-25
```
CANONICAL
```
entity.legal_name = "ALCON LABORATORIES (AUSTRALIA) PTY LTD"    (raw: "ALCON LABORATORIES (AUSTRALIA) PTY LTD", field_confidence: 0.9)
entity.abn = "88000740830"    (raw: "88000740830", field_confidence: 0.95)
```

### Example 4 — source_record_id ALLIED CREDIT PTY LTD|2024-25
RAW
```
Name: ALLIED CREDIT PTY LTD
ABN: 65143964667
Total income $: 297051241
Taxable income $: 
Tax payable $: 
Income year: 2024-25
```
CANONICAL
```
entity.legal_name = "ALLIED CREDIT PTY LTD"    (raw: "ALLIED CREDIT PTY LTD", field_confidence: 0.9)
entity.abn = "65143964667"    (raw: "65143964667", field_confidence: 0.95)
```

### Example 5 — source_record_id AVJENNINGS LIMITED|2024-25
RAW
```
Name: AVJENNINGS LIMITED
ABN: 44004327771
Total income $: 254590674
Taxable income $: 17470140
Tax payable $: 5241042
Income year: 2024-25
```
CANONICAL
```
entity.legal_name = "AVJENNINGS LIMITED"    (raw: "AVJENNINGS LIMITED", field_confidence: 0.9)
entity.abn = "44004327771"    (raw: "44004327771", field_confidence: 0.95)
```

## Your decision

Run exactly one of:

    firm onboard corporate-transparency --decide "approve"
    firm onboard corporate-transparency --decide "reject: <what is wrong and what to use instead>"
    firm onboard corporate-transparency --decide "abandon"

You never edit the config directly — a hand-edited config is hand-authored, and
the point is that it is not. Reject with a comment instead.