# Mapping review — asic-business-names

| | |
|---|---|
| Dataset | asic-business-names — ASIC - Business Names Dataset |
| Publisher / licence | Australian Securities and Investments Commission (ASIC) / cc-by |
| Resource | https://data.gov.au/data/dataset/bc515135-4bb6-4d50-957a-3713709a76d3/resource/55ad4b1c-5eeb-44ea-8b29-d410da431be3/download/business_names_202610.csv |
| Reader | {"format": "tsv", "delimiter": "\t", "encoding": "utf-8-sig", "header_row": 0, "sheet": null} |
| Agent run | revisions used 0/3 · steps 5 |
| **Status** | **PASSING WITH FLAGS** |
| Source reliability | 0.9 — ASIC is the national regulator and this is its own Business Names Register published under CC-BY, so it is authoritative for name, status and ABN claims. |
| Record id | row_hash [] — No unique source record key exists: BN_STATE_NUM is 96% null, and BN_ABN is 16% null and can repeat when one holder has several business names. BN_NAME is 200/200 distinct in the sample but is not guaranteed unique across the full register, so row_hash over the whole row is the safe choice. |
| Observed at | dataset_modified → 2026-10-13 (basis: proxy) — The dataset has no per-record extract or last-updated column. BN_REG_DT and BN_CANCEL_DT are registration and cancellation dates (valid_from material), not times ASIC asserted the record. So dataset_modified is used as a weak proxy, with basis proxy. |

## Mapping (3 field mappings from 8 source columns)

| canonical | ← source column | transforms | conf. | cond. | evidence |
|---|---|---|---|---|---|
| entity.trading_name | BN_NAME | `["trim", "empty_to_null"]` | 0.85 |  | BN_NAME holds values like ' SA Super Quiz', ' KB Freightlines' and ' Big C's Texas BBQ' (200 distinct of 200, 0% null). These are registered business names, which are trading names, not the holder's legal name, so this i |
| entity.abn | BN_ABN | `["trim", "empty_to_null", "strip_float_suffix", "digits_only", "abn_normalize"]` | 0.9 |  | BN_ABN holds values like '36437438294' and '94212794661', all 11-digit. It is the ABN of the business name holder. Blank on Deregistered rows (16% null), which become absence, not errors. BN_STATE_NUM is a different iden |
| entity.status | BN_STATUS | `["trim", {"map_enum": {"mapping": {"Registered": "active", "Deregistered": "deregistered"}, "default": "unknown"}}]` | 0.8 |  | BN_STATUS has two distinct values, 'Registered' and 'Deregistered'. They are the registration status of the business name record, and I map them to active and deregistered respectively. Rows with a BN_CANCEL_DT carry 'De |

## Validation — 350 held-out rows (loop set; final acceptance runs once after approval)

| check | threshold | result | pass |
|---|---|---|---|
| identifier checksum (entity.abn) | >= 95% | 100.0% (292 ok / 0 failed) | ✅ |
| enum legality (entity.status) | >= 98% | 100.0% (350 ok / 0 failed) | ✅ |
| null drift (entity.trading_name ← BN_NAME) | <= +2pp | +0.0% | ✅ |
| null drift (entity.abn ← BN_ABN) | <= +2pp | +0.0% | ✅ |
| null drift (entity.status ← BN_STATUS) | <= +2pp | +0.0% | ✅ |
| record_id unique (full sample) | 0 duplicates | 0 duplicates | ✅ |
| minimum useful (a name or an identifier mapped) | required | yes | ✅ |

### Failing examples
none

## Semantic spot-check — 10 held-out records: 18 ok, 10 suspicious

| record | field | verdict | why |
|---|---|---|---|
| 32c724c2dbbb3583 | entity.trading_name | ok | BN_NAME 'Hair Design by Tracey' is a registered business name, so trading_name is the right field, and trim only removed leading whitespace. |
| 32c724c2dbbb3583 | entity.status | suspicious | BN_STATUS 'Deregistered' (BN_CANCEL_DT 08/10/2025) describes the business-name registration being cancelled, not the holder entity being deregistered, so mappin |
| c5bf3049b783ed80 | entity.trading_name | ok | 'Spice Alley Harris Park' is a business name, which fits trading_name. |
| c5bf3049b783ed80 | entity.abn | ok | BN_ABN is the name holder's ABN, which is the subject entity, and the 11-digit value passes the ABN checksum. |
| c5bf3049b783ed80 | entity.status | suspicious | 'Registered' means the business name registration is current, not that the holder entity is active, so mapping it to 'active' conflates the two. |
| 26657e231e46f8fe | entity.trading_name | ok | 'SANAE BY R' is a registered business name, so trading_name fits. |
| 26657e231e46f8fe | entity.abn | ok | The value is the holder's ABN from BN_ABN and passes the checksum. |
| 26657e231e46f8fe | entity.status | suspicious | The name registration is current (registered 02/12/2025), which says nothing about the holder entity's status. |
| c4177191d6ebe145 | entity.trading_name | ok | 'Metlaser Designs' is a business name and belongs in trading_name. |
| c4177191d6ebe145 | entity.abn | ok | BN_ABN is the holder's ABN and the value passes the checksum. |
| c4177191d6ebe145 | entity.status | suspicious | 'Registered' describes the business name record, not the entity, so 'active' is an overreach. |
| cf6f159552d2c33d | entity.trading_name | ok | 'DE'LISH FARM FRESH FRUIT AND VEGETABLES' is a business name, and the apostrophe is preserved. |
| cf6f159552d2c33d | entity.abn | ok | BN_ABN is the holder's ABN and the value passes the checksum. |
| cf6f159552d2c33d | entity.status | suspicious | The name registration being current is mapped to entity-level 'active', which is a different meaning. |
| 964b97451faea954 | entity.trading_name | ok | 'iCre8-e' is a business name and fits trading_name. |
| 964b97451faea954 | entity.abn | ok | BN_ABN is the 11-digit ABN of the name holder, which is the subject entity. |
| 964b97451faea954 | entity.status | suspicious | 'Registered' is the status of the business name, not of the company or person holding it. |
| 50ea5823b52d6a03 | entity.trading_name | ok | 'WM Demolition Services' is a business name, so trading_name fits. |
| 50ea5823b52d6a03 | entity.abn | ok | BN_ABN is the holder's ABN, which is the right party. |
| 50ea5823b52d6a03 | entity.status | suspicious | The name registration being current does not mean the holder entity is active. |
| 91540a37b06c301e | entity.trading_name | ok | 'EBV - East Brunswick Village' is a registered business name, which fits trading_name. |
| 91540a37b06c301e | entity.abn | ok | BN_ABN is the name holder's ABN and is 11 digits. |
| 91540a37b06c301e | entity.status | suspicious | BN_STATUS is the status of the business name registration, not of the entity. |
| c17402c3ba3ea282 | entity.trading_name | ok | 'Glynn Delley Fitness' is a business name, so trading_name fits. |
| c17402c3ba3ea282 | entity.abn | ok | BN_ABN is the holder's ABN and is 11 digits. |
| c17402c3ba3ea282 | entity.status | suspicious | A current name registration is mapped to entity 'active', which conflates the registration with the holder. |
| 931d8725db56641f | entity.trading_name | ok | 'THE POPPY CENTRE' is a business name, so trading_name fits. |
| 931d8725db56641f | entity.status | suspicious | 'Deregistered' with BN_CANCEL_DT 08/01/2026 means the business name was cancelled, and the holder may still be a trading entity, so 'deregistered' is wrong at e |

Notes: The BN_STATUS to entity.status mapping is the systemic problem. Every record is affected, because Registered/Deregistered describe the business-name registration, not the holder entity's existence. 'Deregistered' is especially harmful, since a cancelled name does not mean the holder entity is deregistered. Map it to unknown, or drop it, or use a name-registration-specific field if one exists.; BN_REG_DT and BN_CANCEL_DT are unmapped, which is correct: they are name registration dates, not entity.date_registered.; The register has no legal-name column, so entity.legal_name is never populated. BN_ABN is the only link to the holder, and deregistered rows have no ABN, which leaves them with no identifier.; BN_STATE_NUM and BN_STATE_OF_REG were blank in all 10 held-out records, so the evidence note about 'BN98583878' values could not be checked on this sample.

## Unmapped columns (5)

| source column | reason |
|---|---|
| REGISTER_NAME | Constant 'BUSINESS NAMES' on every row (1 distinct); it names the register and carries no entity attribute. |
| BN_REG_DT | Date the business name was registered (e.g. 22/10/2019), not the date the holding entity was registered, so it would be wrong as entity.date_registered. It is valid_from material for the name, which has no ontology field, and it is not observed_at. |
| BN_CANCEL_DT | Cancellation date of the business name (86% null, only on Deregistered rows). No ontology field; it is not a per-record extract date, so not observed_at. |
| BN_STATE_NUM | Legacy state-issued business name registration number (e.g. 'BN98583878', 'B2163216W'), 96% null. It is not an ABN or ACN and has no ontology field. |
| BN_STATE_OF_REG | State where the name was originally registered (NSW/VIC/QLD, 96% null), not the holder's address. Mapping it to address.state would be speculative. |

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
entity.status = "active"    (raw: "Registered", field_confidence: 0.8)
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
entity.status = "active"    (raw: "Registered", field_confidence: 0.8)
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
entity.status = "deregistered"    (raw: "Deregistered", field_confidence: 0.8)
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
entity.status = "active"    (raw: "Registered", field_confidence: 0.8)
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
entity.status = "active"    (raw: "Registered", field_confidence: 0.8)
```

## Your decision

Run exactly one of:

    firm onboard asic-business-names --decide "approve"
    firm onboard asic-business-names --decide "reject: <what is wrong and what to use instead>"
    firm onboard asic-business-names --decide "abandon"

You never edit the config directly — a hand-edited config is hand-authored, and
the point is that it is not. Reject with a comment instead.