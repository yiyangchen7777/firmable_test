# Mapping review — corporate-transparency

| | |
|---|---|
| Dataset | corporate-transparency — Corporate Tax Transparency |
| Publisher / licence | Australian Taxation Office / cc-by |
| Resource | https://data.gov.au/data/dataset/c2524c87-cea4-4636-acac-599a82048a26/resource/15bf4eaa-7a14-48e9-8a3f-092df32a644e/download/2024-25-corporate-report-of-entity-tax-information.xlsx |
| Reader | {"format": "xlsx", "delimiter": null, "encoding": "utf-8", "header_row": 0, "sheet": "Income tax details"} |
| Agent run | revisions used 0/3 · steps 5 |
| **Status** | **PASSING** |
| Source reliability | 0.9 — The ATO is the national tax regulator publishing its own corporate tax transparency report under CC-BY, so names and ABNs are authoritative. |
| Record id | column ['Name'] — The report has no record key and the ABN is nullable (1.5% blank, 197 distinct over 200 rows), so ABN alone is not unique. The Name column is 100% populated with 200 distinct values across 200 rows. Each entity appears once per income year, and the sample covers a single year, so Name is unique per record. |
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
| record_id unique (full sample) | 0 duplicates | 0 duplicates | ✅ |
| minimum useful (a name or an identifier mapped) | required | yes | ✅ |

### Failing examples
none

## Semantic spot-check — 10 held-out records: 20 ok, 0 suspicious

| record | field | verdict | why |
|---|---|---|---|
| AUSPORK LIMITED | entity.legal_name | ok | 'Name' in a tax-entity report holds the registered corporate name 'AUSPORK LIMITED', and no other party column exists. |
| AUSPORK LIMITED | entity.abn | ok | The ABN 38006563355 passes the mod-89 checksum and belongs to the row's own entity. |
| BEST FAB PTY LTD | entity.legal_name | ok | 'BEST FAB PTY LTD' is a registered-style company name with a PTY LTD suffix. |
| BEST FAB PTY LTD | entity.abn | ok | The ABN 83105906876 passes the mod-89 checksum, and the row has no other party's identifier. |
| BENDIGO AND ADELAIDE BANK LIMITED | entity.legal_name | ok | This is the registered name of the bank, not a brand name. |
| BENDIGO AND ADELAIDE BANK LIMITED | entity.abn | ok | The ABN 11068049178 passes the mod-89 checksum. |
| AVENG AUSTRALIA HOLDINGS PTY LTD | entity.legal_name | ok | The raw 'Name' is the entity's own registered name. 'Holdings' is part of that name and does not mean a parent company was substituted. |
| AVENG AUSTRALIA HOLDINGS PTY LTD | entity.abn | ok | The ABN 33108058331 passes the mod-89 checksum. |
| APS GROUP (HOLDINGS) PTY LTD | entity.legal_name | ok | The name is copied verbatim, including the parentheses, and is a registered company name. |
| APS GROUP (HOLDINGS) PTY LTD | entity.abn | ok | The ABN 94096418101 passes the mod-89 checksum. |
| BARALABA COAL COMPANY PTY LTD | entity.legal_name | ok | This is a registered company name with a PTY LTD suffix. |
| BARALABA COAL COMPANY PTY LTD | entity.abn | ok | The ABN 42096909634 passes the mod-89 checksum. |
| BNC GLOBAL INVESTMENTS PTY LTD | entity.legal_name | ok | This is a registered company name with a PTY LTD suffix. |
| BNC GLOBAL INVESTMENTS PTY LTD | entity.abn | ok | The ABN 39618091517 passes the mod-89 checksum. |
| AMENTUM AUSTRALIA PROPRIETARY LIMITED | entity.legal_name | ok | 'PROPRIETARY LIMITED' is the long form of a registered company suffix, so this is a legal name. |
| AMENTUM AUSTRALIA PROPRIETARY LIMITED | entity.abn | ok | The ABN 12079749287 passes the mod-89 checksum. |
| ARCHIES FOOTWEAR PTY LTD | entity.legal_name | ok | The PTY LTD suffix marks this as the registered entity, not the 'Archies' brand. |
| ARCHIES FOOTWEAR PTY LTD | entity.abn | ok | The ABN 91164576854 passes the mod-89 checksum. |
| BGC (AUSTRALIA) PTY LTD | entity.legal_name | ok | This is a registered company name copied verbatim. |
| BGC (AUSTRALIA) PTY LTD | entity.abn | ok | The ABN 62005736005 passes the mod-89 checksum. |

Notes: All 10 ABNs are 11 digits and pass the mod-89 checksum.; Every 'Name' value carries a corporate suffix (LIMITED, PTY LTD, PROPRIETARY LIMITED). None looks like a trading name or a person.; The unmapped columns (Total income, Taxable income, Tax payable, Income year) are financial figures. None is a party name, an alternate identifier or a registration date, so nothing was mis-mapped.; The source is a tax-transparency report. The mapping correctly avoids deriving entity.status, entity.date_registered or an address from it.

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

### Example 1 — source_record_id AUSTRALIAN POSTAL CORPORATION
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

### Example 2 — source_record_id AUSTRALIAN LOGISTICS ACQUISITION HOLDINGS PTY LTD
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

### Example 3 — source_record_id ALCON LABORATORIES (AUSTRALIA) PTY LTD
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

### Example 4 — source_record_id ALLIED CREDIT PTY LTD
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

### Example 5 — source_record_id AVJENNINGS LIMITED
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