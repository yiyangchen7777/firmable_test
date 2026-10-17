# Mapping review — asic-business-names

| | |
|---|---|
| Dataset | asic-business-names — ASIC - Business Names Dataset |
| Publisher / licence | Australian Securities and Investments Commission (ASIC) / cc-by |
| Resource | https://data.gov.au/data/dataset/bc515135-4bb6-4d50-957a-3713709a76d3/resource/55ad4b1c-5eeb-44ea-8b29-d410da431be3/download/business_names_202610.csv |
| Reader | {"format": "tsv", "delimiter": "\t", "encoding": "utf-8-sig", "header_row": 0, "sheet": null} |
| Agent run | revisions used 1/3 · steps 8 |
| **Status** | **PASSING** |
| Source reliability | 0.9 — ASIC is the national regulator and this is its own Business Names Register published under CC-BY, so it is authoritative for name, status and ABN claims. |
| Record id | row_hash [] — No unique source record key exists: BN_STATE_NUM is 96% null, and BN_ABN is 16% null and can repeat when one holder has several business names. BN_NAME is 200/200 distinct in the sample but is not guaranteed unique across the full register, so row_hash over the whole row is the safe choice. |
| Observed at | dataset_modified → 2026-10-13 (basis: proxy) — The dataset has no per-record extract or last-updated column. BN_REG_DT and BN_CANCEL_DT are registration and cancellation dates (valid_from material), not times ASIC asserted the record. So dataset_modified is used as a weak proxy, with basis proxy. |

## Mapping (2 field mappings from 8 source columns)

| canonical | ← source column | transforms | conf. | cond. | evidence |
|---|---|---|---|---|---|
| entity.trading_name | BN_NAME | `["trim", "empty_to_null"]` | 0.85 |  | BN_NAME holds values like ' SA Super Quiz', ' KB Freightlines' and ' Big C's Texas BBQ' (200 distinct of 200, 0% null). These are registered business names, which are trading names, not the holder's legal name, so this i |
| entity.abn | BN_ABN | `["trim", "empty_to_null", "strip_float_suffix", "digits_only", "abn_normalize"]` | 0.9 |  | BN_ABN holds values like '36437438294' and '94212794661', all 11-digit. It is the ABN of the business name holder. Blank on Deregistered rows (16% null), which become absence, not errors. BN_STATE_NUM is a different iden |

## Validation — 350 held-out rows (loop set; final acceptance runs once after approval)

| check | threshold | result | pass |
|---|---|---|---|
| identifier checksum (entity.abn) | >= 95% | 100.0% (292 ok / 0 failed) | ✅ |
| null drift (entity.trading_name ← BN_NAME) | <= +2pp | +0.0% | ✅ |
| null drift (entity.abn ← BN_ABN) | <= +2pp | +0.0% | ✅ |
| record_id effectively unique (full sample) | <= 0.5% duplicates | 0 duplicates (0.00%) | ✅ |
| minimum useful (a name or an identifier mapped) | required | yes | ✅ |

### Failing examples
none

## Semantic spot-check — 10 held-out records: 18 ok, 0 suspicious

| record | field | verdict | why |
|---|---|---|---|
| 32c724c2dbbb3583 | entity.trading_name | ok | BN_NAME ' Hair Design by Tracey' is a registered business name, so it is a trading name, and trim only removed the leading space. |
| c5bf3049b783ed80 | entity.trading_name | ok | BN_NAME 'Spice Alley Harris Park' is a business name, so it is a trading name. |
| c5bf3049b783ed80 | entity.abn | ok | BN_ABN is the business name holder's ABN, and 97126071878 passes the ABN checksum. |
| 26657e231e46f8fe | entity.trading_name | ok | 'SANAE BY R' is a brand-style business name, correctly kept as a trading name. |
| 26657e231e46f8fe | entity.abn | ok | BN_ABN is the holder's ABN, and 34136548659 passes the checksum. |
| c4177191d6ebe145 | entity.trading_name | ok | 'Metlaser Designs' is a registered business name, so it is a trading name. |
| c4177191d6ebe145 | entity.abn | ok | BN_ABN is the holder's ABN, and 68837016304 passes the checksum. |
| cf6f159552d2c33d | entity.trading_name | ok | 'DE'LISH FARM FRESH FRUIT AND VEGETABLES' is a business name, not a legal name, and the apostrophe was preserved. |
| cf6f159552d2c33d | entity.abn | ok | BN_ABN is the holder's ABN, and 35069234900 passes the checksum. |
| 964b97451faea954 | entity.trading_name | ok | 'iCre8-e' is a brand-style business name, correctly kept as a trading name. |
| 964b97451faea954 | entity.abn | ok | BN_ABN is the holder's ABN, and 68213665343 passes the checksum. |
| 50ea5823b52d6a03 | entity.trading_name | ok | 'WM Demolition Services' is a registered business name, so it is a trading name. |
| 50ea5823b52d6a03 | entity.abn | ok | BN_ABN is the holder's ABN, and 74586960761 passes the checksum. |
| 91540a37b06c301e | entity.trading_name | ok | 'EBV - East Brunswick Village' is a business name, so it is a trading name. |
| 91540a37b06c301e | entity.abn | ok | BN_ABN is the holder's ABN, and 13147061372 passes the checksum. |
| c17402c3ba3ea282 | entity.trading_name | ok | 'Glynn Delley Fitness' is a registered business name containing a person's name, which is still a trading name and not the holder's legal name. |
| c17402c3ba3ea282 | entity.abn | ok | BN_ABN is the holder's ABN, and 29664401020 passes the checksum. |
| 931d8725db56641f | entity.trading_name | ok | 'THE POPPY CENTRE' is a business name, correctly a trading name. The row is Deregistered and BN_ABN is blank, so no ABN claim was produced. |

Notes: All 8 ABNs present in the sample pass the ABN checksum, and BN_ABN consistently identifies the business name holder.; The register has no legal-name column, so no entity.legal_name claim is produced. That is correct, since BN_NAME is a trading name.; BN_STATUS, BN_REG_DT and BN_CANCEL_DT are unmapped. This avoids the date and status semantic traps, because BN_REG_DT is the business-name registration date, not the entity's, and 'Registered' describes the name, not the company.; Leading whitespace on BN_NAME is consistently trimmed.

## Unmapped columns (6)

| source column | reason |
|---|---|
| REGISTER_NAME | Constant 'BUSINESS NAMES' on every row (1 distinct); it names the register and carries no entity attribute. |
| BN_REG_DT | Date the business name was registered (e.g. 22/10/2019). It is valid_from material for the name claim, which this engine does not yet carry. It is not the holder's registration date, so it would be wrong as entity.date_registered, and it is not observed_at. |
| BN_CANCEL_DT | Cancellation date of the business name (86% null, only on Deregistered rows). It is valid_to material for the name claim, which this engine does not yet carry. It is not a per-record extract date, so not observed_at. |
| BN_STATE_NUM | Legacy state-issued business name registration number (e.g. 'BN98583878', 'B2163216W'), 96% null. It is not an ABN or ACN and has no ontology field. |
| BN_STATE_OF_REG | State where the name was originally registered (NSW/VIC/QLD, 96% null), not the holder's address. Mapping it to address.state would be speculative. |
| BN_STATUS | Status of the business-name registration ('Registered'/'Deregistered'), not of the holder entity. A cancelled name does not mean the holder is deregistered (e.g. a no-ABN row like 'Curry Festival' would wrongly emit entity.status=deregistered). Unmapped per human review and semantic flags. |

## Side-by-side — 5 raw records vs their canonical observations

Read these for meaning, not parse success: is the date a registration date or a
licence date? Is the name the licensee or the applicant? Is the ABN the subject
entity's?

### Example 1 — source_record_id 62de9a8f2a3895f2
RAW
```
REGISTER_NAME: BUSINESS NAMES
BN_NAME:  PLATINUM STRATA
BN_STATUS: Registered
BN_REG_DT: 16/03/2021
BN_CANCEL_DT: 
BN_STATE_NUM: 
BN_STATE_OF_REG: 
BN_ABN: 78141479160
```
CANONICAL
```
entity.trading_name = "PLATINUM STRATA"    (raw: " PLATINUM STRATA", field_confidence: 0.85)
entity.abn = "78141479160"    (raw: "78141479160", field_confidence: 0.9)
```

### Example 2 — source_record_id 5edaec7f0dff8924
RAW
```
REGISTER_NAME: BUSINESS NAMES
BN_NAME:  NORTH Link Networking for Economic Development
BN_STATUS: Registered
BN_REG_DT: 28/11/2018
BN_CANCEL_DT: 
BN_STATE_NUM: 
BN_STATE_OF_REG: 
BN_ABN: 23226473941
```
CANONICAL
```
entity.trading_name = "NORTH Link Networking for Economic Development"    (raw: " NORTH Link Networking for Economic Deve", field_confidence: 0.85)
entity.abn = "23226473941"    (raw: "23226473941", field_confidence: 0.9)
```

### Example 3 — source_record_id b8919a1e0a90d823
RAW
```
REGISTER_NAME: BUSINESS NAMES
BN_NAME:  Curry Festival
BN_STATUS: Deregistered
BN_REG_DT: 25/02/2015
BN_CANCEL_DT: 09/04/2026
BN_STATE_NUM: 
BN_STATE_OF_REG: 
BN_ABN: 
```
CANONICAL
```
entity.trading_name = "Curry Festival"    (raw: " Curry Festival", field_confidence: 0.85)
```

### Example 4 — source_record_id e48f205ea9ea72a2
RAW
```
REGISTER_NAME: BUSINESS NAMES
BN_NAME:  G & A TILING
BN_STATUS: Registered
BN_REG_DT: 09/09/2005
BN_CANCEL_DT: 
BN_STATE_NUM: B1866952P
BN_STATE_OF_REG: VIC
BN_ABN: 
```
CANONICAL
```
entity.trading_name = "G & A TILING"    (raw: " G & A TILING", field_confidence: 0.85)
```

### Example 5 — source_record_id 92ec036b0af4bdbb
RAW
```
REGISTER_NAME: BUSINESS NAMES
BN_NAME:  MSA PLASTERING SERVICES
BN_STATUS: Registered
BN_REG_DT: 03/02/2021
BN_CANCEL_DT: 
BN_STATE_NUM: 
BN_STATE_OF_REG: 
BN_ABN: 96885381486
```
CANONICAL
```
entity.trading_name = "MSA PLASTERING SERVICES"    (raw: " MSA PLASTERING SERVICES", field_confidence: 0.85)
entity.abn = "96885381486"    (raw: "96885381486", field_confidence: 0.9)
```

## Your decision

Run exactly one of:

    firm onboard asic-business-names --decide "approve"
    firm onboard asic-business-names --decide "reject: <what is wrong and what to use instead>"
    firm onboard asic-business-names --decide "abandon"

You never edit the config directly — a hand-edited config is hand-authored, and
the point is that it is not. Reject with a comment instead.