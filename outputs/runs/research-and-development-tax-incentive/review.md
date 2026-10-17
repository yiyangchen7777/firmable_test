# Mapping review — research-and-development-tax-incentive

| | |
|---|---|
| Dataset | research-and-development-tax-incentive — Research and Development tax incentive |
| Publisher / licence | Australian Taxation Office / cc-by-2.5 |
| Resource | https://data.gov.au/data/dataset/7c356598-b048-4c1e-862f-c936041e3d81/resource/5f7d5cac-cfa8-4500-8468-1c396f3a08d1/download/report-of-information-about-research-and-development-tax-incentive-entities-2023-24.xlsx |
| Reader | {"format": "xlsx", "delimiter": null, "encoding": "utf-8-sig", "header_row": 0, "sheet": "2023-24 Report"} |
| Agent run | revisions used 0/3 · steps 5 |
| **Status** | **PASSING** |
| Source reliability | 0.9 — The ATO is the national tax regulator publishing R&D tax incentive entity data from its own administrative records under an open CC-BY licence, so names and ABNs are authoritative. |
| Record id | column ['ABN/ACN'] — The source has no record key of its own. Each ABN appears once in this report (200 distinct values over 200 rows, null rate 0), with one row per entity for the single income year 2023-24. ABN/ACN is therefore unique per record in this sample. The rest of the columns are not needed to distinguish rows. |
| Observed at | dataset_modified → 2026-09-22 (basis: proxy) — No per-record extract or update date exists. Income Year is a constant financial-year label ('2023-24'), not a date the source asserted the record. So the catalogue modified date is used as a weak proxy (dataset_modified, basis proxy), with format null. |

## Mapping (3 field mappings from 5 source columns)

| canonical | ← source column | transforms | conf. | cond. | evidence |
|---|---|---|---|---|---|
| entity.legal_name | Company name | `["trim", "empty_to_null"]` | 0.9 |  | Column 'Company name' holds values like 'AESON POWER PTY LTD', 'AINSWORTH GAME TECHNOLOGY LIMITED' and 'A.C.N. 123 310 190 PTY LTD'. These are registered company names including the legal suffix (PTY LTD/LIMITED), so the |
| entity.abn | ABN/ACN | `["strip_float_suffix", "digits_only", {"keep_if_length": 11}, "abn_normalize"]` | 0.9 | yes | Column 'ABN/ACN' has samples such as '94631781121', '41667787500' and '37068516665'. The profile says all 200 values are 11 digits, so they are ABNs and not ACNs. For example, '37123310190' ends in the ACN 123310190 that |
| entity.acn | ABN/ACN | `["strip_float_suffix", "digits_only", {"keep_if_length": 9}, "acn_normalize"]` | 0.85 | yes | Column 'ABN/ACN' is labelled as possibly holding ACNs. No 9-digit values appear in the profile (all are 11-digit, e.g. '94631781121'), so this gated mapping yields no claim on the sampled rows. It is kept as the paired m |

## Validation — 350 held-out rows (loop set; final acceptance runs once after approval)

| check | threshold | result | pass |
|---|---|---|---|
| identifier checksum (entity.abn) | >= 95% | 100.0% (344 ok / 0 failed) | ✅ |
| identifier checksum (entity.acn) | >= 95% | 100.0% (6 ok / 0 failed) | ✅ |
| null drift (entity.legal_name ← Company name) | <= +2pp | +0.0% | ✅ |
| conditional pair coverage (ABN/ACN → entity.abn + entity.acn) | >= 95% of non-null | 100.0% | ✅ |
| record_id effectively unique (full sample) | <= 0.5% duplicates | 0 duplicates in 550 rows (0.00%) | ✅ |
| minimum useful (a name or an identifier mapped) | required | yes | ✅ |

### Failing examples
none

## Semantic spot-check — 10 held-out records: 20 ok, 0 suspicious

| record | field | verdict | why |
|---|---|---|---|
| 73165871910 | entity.legal_name | ok | 'Company name' is the registered name with the PTY LTD suffix, and no other name column exists. |
| 73165871910 | entity.abn | ok | The 11-digit value passes the ABN mod-89 checksum, and it is the only identifier on the row, so it belongs to the named company. |
| 78002831843 | entity.legal_name | ok | The registered company name with suffix, copied verbatim. |
| 78002831843 | entity.abn | ok | The checksum is valid, and the ABN/ACN column holds the subject company's identifier. |
| 23609776892 | entity.legal_name | ok | The registered company name with PTY LTD, and no trading-style or party ambiguity. |
| 23609776892 | entity.abn | ok | The ABN checksum is valid, and the value is the entity's own identifier. |
| 62644190689 | entity.legal_name | ok | 'AGTECHDATA PTY LIMITED' is a registered-style company name. |
| 62644190689 | entity.abn | ok | The checksum is valid, and it is the sole identifier on the row for the same company. |
| 63620070859 | entity.legal_name | ok | 'ACTV STRENGTH CO PTY LTD' carries the legal suffix, so it is the registered name rather than a brand. |
| 63620070859 | entity.abn | ok | The ABN checksum is valid, and the value belongs to the row's company. |
| 48667761659 | entity.legal_name | ok | The registered name with PTY LTD, copied verbatim. |
| 48667761659 | entity.abn | ok | The 11-digit value passes the checksum and is the company's own ABN. |
| 70616406403 | entity.legal_name | ok | The name includes 'HOLDINGS PTY LIMITED', and it is the name of the R&D registrant on this row, not a separate parent column. |
| 70616406403 | entity.abn | ok | The checksum is valid, and there is no separate parent or agent identifier column on the row. |
| 20164400631 | entity.legal_name | ok | The registered company name with PTY LTD. |
| 20164400631 | entity.abn | ok | The ABN checksum is valid, and the value maps to the row's single entity. |
| 94636766320 | entity.legal_name | ok | 'ADATREE PTY LTD' is a registered company name, copied verbatim. |
| 94636766320 | entity.abn | ok | The checksum is valid, and it is the subject company's identifier. |
| 61661992892 | entity.legal_name | ok | The registered company name with the PTY LTD suffix. |
| 61661992892 | entity.abn | ok | The ABN checksum is valid, and the value is the company's own ABN. |

Notes: All 10 ABNs pass the mod-89 checksum, and the 11-digit length gate matches the data. The paired ACN mapping produced no claims, as expected.; The unmapped columns (R&D expenditure, amended expenditure, Income Year) are financial and period data, not identity or date_registered facts, and none were wrongly mapped. 'Income Year' 2023-24 is correctly left out of entity.date_registered.; The source is an R&D-claimant register. Nothing in it supports entity.status or entity_type, and the config correctly maps neither.

## Unmapped columns (3)

| source column | reason |
|---|---|
| Total R&D expenditure (notional deductions less feedstock adjustments) $ | Financial measure (e.g. 102320, 17712107) reported for the income year; no ontology field for expenditure amounts. |
| Total amended R&D expenditure (notional deductions less feedstock adjustments) $ | Financial measure (e.g. 130205, 0), 97.5% null; no ontology field for amended expenditure. |
| Income Year | Single constant value '2023-24' naming the reporting financial year. It is not a per-record extract date and not a registration date, so it fits neither observed_at nor any ontology field. |

## Side-by-side — 5 raw records vs their canonical observations

Read these for meaning, not parse success: is the date a registration date or a
licence date? Is the name the licensee or the applicant? Is the ABN the subject
entity's?

### Example 1 — source_record_id 71641658611
RAW
```
Company name: AGLYTICA PTY LTD
ABN/ACN: 71641658611
Total R&D expenditure (notional deductions less feedstock adjustments) $: 349949
Total amended R&D expenditure (notional deductions less feedstock adjustments) $: 289469
Income Year: 2023-24
```
CANONICAL
```
entity.legal_name = "AGLYTICA PTY LTD"    (raw: "AGLYTICA PTY LTD", field_confidence: 0.9)
entity.abn = "71641658611"    (raw: "71641658611", field_confidence: 0.9)
```

### Example 2 — source_record_id 68626656657
RAW
```
Company name: AGILE 8 PTY LTD
ABN/ACN: 68626656657
Total R&D expenditure (notional deductions less feedstock adjustments) $: 366884
Total amended R&D expenditure (notional deductions less feedstock adjustments) $: 
Income Year: 2023-24
```
CANONICAL
```
entity.legal_name = "AGILE 8 PTY LTD"    (raw: "AGILE 8 PTY LTD", field_confidence: 0.9)
entity.abn = "68626656657"    (raw: "68626656657", field_confidence: 0.9)
```

### Example 3 — source_record_id 16635344419
RAW
```
Company name: ABCURO PTY LTD
ABN/ACN: 16635344419
Total R&D expenditure (notional deductions less feedstock adjustments) $: 3062525
Total amended R&D expenditure (notional deductions less feedstock adjustments) $: 
Income Year: 2023-24
```
CANONICAL
```
entity.legal_name = "ABCURO PTY LTD"    (raw: "ABCURO PTY LTD", field_confidence: 0.9)
entity.abn = "16635344419"    (raw: "16635344419", field_confidence: 0.9)
```

### Example 4 — source_record_id 29640971553
RAW
```
Company name: ABUNDIUM PTY LIMITED
ABN/ACN: 29640971553
Total R&D expenditure (notional deductions less feedstock adjustments) $: 281800
Total amended R&D expenditure (notional deductions less feedstock adjustments) $: 
Income Year: 2023-24
```
CANONICAL
```
entity.legal_name = "ABUNDIUM PTY LIMITED"    (raw: "ABUNDIUM PTY LIMITED", field_confidence: 0.9)
entity.abn = "29640971553"    (raw: "29640971553", field_confidence: 0.9)
```

### Example 5 — source_record_id 36603065550
RAW
```
Company name: AHS & PARTNERS PTY LTD
ABN/ACN: 36603065550
Total R&D expenditure (notional deductions less feedstock adjustments) $: 67215
Total amended R&D expenditure (notional deductions less feedstock adjustments) $: 
Income Year: 2023-24
```
CANONICAL
```
entity.legal_name = "AHS & PARTNERS PTY LTD"    (raw: "AHS & PARTNERS PTY LTD", field_confidence: 0.9)
entity.abn = "36603065550"    (raw: "36603065550", field_confidence: 0.9)
```

## Your decision

Run exactly one of:

    firm onboard research-and-development-tax-incentive --decide "approve"
    firm onboard research-and-development-tax-incentive --decide "reject: <what is wrong and what to use instead>"
    firm onboard research-and-development-tax-incentive --decide "abandon"

You never edit the config directly — a hand-edited config is hand-authored, and
the point is that it is not. Reject with a comment instead.