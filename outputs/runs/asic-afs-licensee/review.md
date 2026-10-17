# Mapping review — asic-afs-licensee

| | |
|---|---|
| Dataset | asic-afs-licensee — ASIC - Australian Financial Services Licensee Dataset |
| Publisher / licence | Australian Securities and Investments Commission (ASIC) / cc-by |
| Resource | https://data.gov.au/data/dataset/ab7eddce-84df-4098-bc8f-500d0d9776d1/resource/d98a113d-6b50-40e6-b65f-2612efc877f4/download/afs_lic_202610.csv |
| Reader | {"format": "csv", "delimiter": ",", "encoding": "utf-8-sig", "header_row": 0, "sheet": null} |
| Agent run | revisions used 0/3 · steps 5 |
| **Status** | **PASSING** |
| Source reliability | 0.92 — ASIC is the national regulator and this is its own AFS licensee register, published under CC-BY, so it is authoritative for licensee names, identifiers and registered addresses. |
| Record id | column ['AFS_LIC_NUM'] — AFS_LIC_NUM is ASIC's own licence number. It has 200 distinct values across 200 profiled rows and 0% null, so it is unique per record. The ABN could repeat if an entity held several licences, so it is not used. |
| Observed at | dataset_modified → 2026-10-14 (basis: proxy) — No column holds a per-record extract or last-updated date. AFS_LIC_START_DT is the licence start date, which is valid_from material and not when ASIC asserted the record. I therefore use the catalogue modified date (2026-10-14) as a weak dataset-level proxy. |

## Mapping (7 field mappings from 11 source columns)

| canonical | ← source column | transforms | conf. | cond. | evidence |
|---|---|---|---|---|---|
| entity.legal_name | AFS_LIC_NAME | `["trim", "empty_to_null"]` | 0.93 |  | AFS_LIC_NAME holds values such as 'ROXBURGH SECURITIES PTY LTD', 'ACORN CAPITAL LIMITED' and 'NETWEALTH INVESTMENTS LIMITED'. These are registered company names with legal suffixes (PTY LTD, LIMITED), so they are the lic |
| entity.abn | AFS_LIC_ABN_ACN | `["strip_float_suffix", "digits_only", {"keep_if_length": 11}, "abn_normalize"]` | 0.9 | yes | AFS_LIC_ABN_ACN holds values such as '33004739655', '83009199740' and '52089240513', all 11 digits. That is the ABN shape and not the 9-digit ACN shape. The column name says ABN or ACN, so the mapping is gated to 11-digi |
| entity.acn | AFS_LIC_ABN_ACN | `["strip_float_suffix", "digits_only", {"keep_if_length": 9}, "acn_normalize"]` | 0.85 | yes | The column name AFS_LIC_ABN_ACN allows ACNs. Any 9-digit value such as a stripped-zero ACN would be captured here, and the 11-digit samples ('33004739655', '83009199740') yield no claim. Absence on most rows is intended, |
| address.locality | AFS_LIC_ADD_LOCAL | `["trim", "empty_to_null"]` | 0.93 |  | AFS_LIC_ADD_LOCAL holds suburb or city names such as 'MELBOURNE', 'DALKEITH' and 'NORTH FREMANTLE', and each is consistent with its adjacent state and postcode columns. These are localities in the licensee's address. |
| address.state | AFS_LIC_ADD_STATE | `["trim", "state_normalize"]` | 0.95 |  | AFS_LIC_ADD_STATE has 5 distinct values ('VIC', 'WA', 'NSW', 'SA', 'QLD'), all standard Australian state abbreviations in the licensee's address block. |
| address.postcode | AFS_LIC_ADD_PCODE | `["trim", "postcode_normalize"]` | 0.93 |  | AFS_LIC_ADD_PCODE holds 4-digit codes such as '3000', '6009' and '2000'. They match the paired locality (MELBOURNE 3000, DALKEITH 6009, SYDNEY 2000), so they are postcodes. Zero-padding protects NT codes like 0800. |
| address.country | AFS_LIC_ADD_COUNTRY | `["trim", "empty_to_null"]` | 0.92 |  | AFS_LIC_ADD_COUNTRY is 'Australia' on every row and sits in the address block alongside locality, state and postcode, so it is the country of the licensee's address. |

## Validation — 350 held-out rows (loop set; final acceptance runs once after approval)

| check | threshold | result | pass |
|---|---|---|---|
| identifier checksum (entity.abn) | >= 95% | 100.0% (345 ok / 0 failed) | ✅ |
| identifier checksum (entity.acn) | >= 95% | 100.0% (5 ok / 0 failed) | ✅ |
| enum legality (address.state) | >= 98% | 100.0% (350 ok / 0 failed) | ✅ |
| null drift (entity.legal_name ← AFS_LIC_NAME) | <= +2pp | +0.0% | ✅ |
| null drift (address.locality ← AFS_LIC_ADD_LOCAL) | <= +2pp | +0.0% | ✅ |
| null drift (address.state ← AFS_LIC_ADD_STATE) | <= +2pp | +0.0% | ✅ |
| null drift (address.postcode ← AFS_LIC_ADD_PCODE) | <= +2pp | +0.0% | ✅ |
| null drift (address.country ← AFS_LIC_ADD_COUNTRY) | <= +2pp | +0.0% | ✅ |
| conditional pair coverage (AFS_LIC_ABN_ACN → entity.abn + entity.acn) | >= 95% of non-null | 100.0% | ✅ |
| record_id effectively unique (full sample) | <= 0.5% duplicates | 0 duplicates (0.00%) | ✅ |
| minimum useful (a name or an identifier mapped) | required | yes | ✅ |

### Failing examples
none

## Semantic spot-check — 10 held-out records: 60 ok, 0 suspicious

| record | field | verdict | why |
|---|---|---|---|
| 233713 | entity.legal_name | ok | AFS_LIC_NAME is the licensee name 'GROVE SECURITIES PTY LTD', a registered company name with a legal suffix. |
| 233713 | entity.abn | ok | AFS_LIC_ABN_ACN is the licensee's own 11-digit ABN, and it passes the ABN checksum. |
| 233713 | address.locality | ok | ALBANY is a suburb or town name and is consistent with WA 6330. |
| 233713 | address.state | ok | WA is a valid state code and matches the locality. |
| 233713 | address.postcode | ok | 6330 is a 4-digit postcode that matches Albany, WA. |
| 233713 | address.country | ok | Australia is the country of the address block. |
| 237757 | entity.legal_name | ok | 'ELDERS RURAL SERVICES AUSTRALIA LIMITED' is the licensee's registered company name. |
| 237757 | entity.abn | ok | It is an 11-digit ABN in the licensee's own column and passes the checksum. |
| 237757 | address.locality | ok | ADELAIDE is a locality and is consistent with SA 5000. |
| 237757 | address.state | ok | SA is a valid state code and matches Adelaide. |
| 237757 | address.postcode | ok | 5000 is the Adelaide postcode. |
| 237757 | address.country | ok | Australia is the country of the address block. |
| 237556 | entity.legal_name | ok | 'IRONBRIDGE CAPITAL MANAGEMENT PTY LIMITED' is the licensee's company name. |
| 237556 | entity.abn | ok | It is the licensee's 11-digit ABN and passes the checksum. |
| 237556 | address.locality | ok | SYDNEY is a locality and is consistent with NSW 2000. |
| 237556 | address.state | ok | NSW is a valid state code and matches Sydney. |
| 237556 | address.postcode | ok | 2000 is the Sydney postcode. |
| 237556 | address.country | ok | Australia is the country of the address block. |
| 235017 | entity.legal_name | ok | 'METROPOLIS PTY. LTD.' is the licensee's registered name with a legal suffix, not a brand name. |
| 235017 | entity.abn | ok | It is the licensee's 11-digit ABN from the ABN/ACN column. |
| 235017 | address.locality | ok | PORT MELBOURNE is a suburb and is consistent with VIC 3207. |
| 235017 | address.state | ok | VIC is a valid state code and matches the locality. |
| 235017 | address.postcode | ok | 3207 is the Port Melbourne postcode. |
| 235017 | address.country | ok | Australia is the country of the address block. |
| 230251 | entity.legal_name | ok | 'YARRA FUNDS MANAGEMENT LIMITED' is the licensee's company name. |
| 230251 | entity.abn | ok | It is an 11-digit ABN in the licensee's own column. |
| 230251 | address.locality | ok | MELBOURNE is a locality and is consistent with VIC 3000. |
| 230251 | address.state | ok | VIC is a valid state code and matches Melbourne. |
| 230251 | address.postcode | ok | 3000 is the Melbourne postcode. |
| 230251 | address.country | ok | Australia is the country of the address block. |
| 236776 | entity.legal_name | ok | 'AUSTRALIAN PRIVATE CAPITAL ADVISORY SERVICES PTY. LTD.' is the licensee's registered company name. |
| 236776 | entity.abn | ok | It is the licensee's 11-digit ABN from the ABN/ACN column. |
| 236776 | address.locality | ok | MELBOURNE is a locality and is consistent with VIC 3000. |
| 236776 | address.state | ok | VIC is a valid state code and matches the locality. |
| 236776 | address.postcode | ok | 3000 is the Melbourne postcode. |
| 236776 | address.country | ok | Australia is the country of the address block. |
| 238268 | entity.legal_name | ok | 'ANZ STAFF SUPERANNUATION (AUSTRALIA) PTY. LIMITED' is the licensee entity name. It is a distinct company, not the parent bank. |
| 238268 | entity.abn | ok | It is an 11-digit ABN in the licensee's own column. |
| 238268 | address.locality | ok | DOCKLANDS is a Melbourne suburb and is consistent with VIC 3008. |
| 238268 | address.state | ok | VIC is a valid state code and matches Docklands. |
| 238268 | address.postcode | ok | 3008 is the Docklands postcode. |
| 238268 | address.country | ok | Australia is the country of the address block. |
| 229170 | entity.legal_name | ok | 'INTERFINANZ PTY LTD' is the licensee's registered name with a legal suffix. |
| 229170 | entity.abn | ok | It is an 11-digit ABN from the licensee's ABN/ACN column. |
| 229170 | address.locality | ok | COLLINGWOOD is a Melbourne suburb and is consistent with VIC 3066. |
| 229170 | address.state | ok | VIC is a valid state code and matches Collingwood. |
| 229170 | address.postcode | ok | 3066 is the Collingwood postcode. |
| 229170 | address.country | ok | Australia is the country of the address block. |
| 230557 | entity.legal_name | ok | 'TFS AUSTRALIA PTY. LIMITED' is the licensee's company name. |
| 230557 | entity.abn | ok | It is an 11-digit ABN in the licensee's own column. |
| 230557 | address.locality | ok | SYDNEY is a locality and is consistent with NSW 2000. |
| 230557 | address.state | ok | NSW is a valid state code and matches Sydney. |
| 230557 | address.postcode | ok | 2000 is the Sydney postcode. |
| 230557 | address.country | ok | Australia is the country of the address block. |
| 237848 | entity.legal_name | ok | 'TAL LIFE LIMITED' is the licensee's registered company name. |
| 237848 | entity.abn | ok | It is the licensee's 11-digit ABN from the ABN/ACN column. |
| 237848 | address.locality | ok | SYDNEY is a locality and is consistent with NSW 2000. |
| 237848 | address.state | ok | NSW is a valid state code and matches Sydney. |
| 237848 | address.postcode | ok | 2000 is the Sydney postcode. |
| 237848 | address.country | ok | Australia is the country of the address block. |

Notes: none: AFS_LIC_START_DT (licence start date) is correctly left unmapped and is not used as entity.date_registered.; The unmapped columns (AFS_LIC_NUM, AFS_LIC_PRE_FSR, AFS_LIC_CONDITION, REGISTER_NAME) are licence metadata and do not conflict with any mapped field.; The register does not say whether the address is a business, postal or registered-office address. It is consistently the licensee's address, so this is not flagged.

## Unmapped columns (5)

| source column | reason |
|---|---|
| REGISTER_NAME | Constant 'AFS Licence' on every row (1 distinct value). It names the register and describes no entity, so there is no ontology field. |
| AFS_LIC_NUM | The licence number is the record key, used for record_id. It is not an entity identifier such as ABN, ACN or NZBN, so no ontology field exists. |
| AFS_LIC_START_DT | dd/mm/yyyy dates such as '24/04/2003' and '13/08/2003' (day above 12 confirms day-first) are the licence start date. They are not entity.date_registered, which would be the company's incorporation date, and they are valid_from material, so mapping would be wrong. |
| AFS_LIC_PRE_FSR | Holds the pre-Financial Services Reform licence type and number as a quoted string, e.g. '"Securities dealer","000191662"'. It is a licence relationship attribute with no ontology field, and it is 28.5% null. |
| AFS_LIC_CONDITION | Free-text licence authorisation or conditions ('This licence authorises the licensee to carry on a financial services business...'). This is licence detail with no ontology field. |

## Side-by-side — 5 raw records vs their canonical observations

Read these for meaning, not parse success: is the date a registration date or a
licence date? Is the name the licensee or the applicant? Is the ABN the subject
entity's?

### Example 1 — source_record_id 234599
RAW
```
REGISTER_NAME: AFS Licence
AFS_LIC_NUM: 234599
AFS_LIC_NAME: UTILITIES OF AUSTRALIA PTY LTD
AFS_LIC_ABN_ACN: 55063384127
AFS_LIC_START_DT: 03/03/2004
AFS_LIC_PRE_FSR: 
AFS_LIC_ADD_LOCAL: SYDNEY
AFS_LIC_ADD_STATE: NSW
AFS_LIC_ADD_PCODE: 2000
AFS_LIC_ADD_COUNTRY: Australia
AFS_LIC_CONDITION: "This licence authorises the licensee to carry on a financial services
```
CANONICAL
```
entity.legal_name = "UTILITIES OF AUSTRALIA PTY LTD"    (raw: "UTILITIES OF AUSTRALIA PTY LTD", field_confidence: 0.93)
entity.abn = "55063384127"    (raw: "55063384127", field_confidence: 0.9)
address.locality = "SYDNEY"    (raw: "SYDNEY", field_confidence: 0.93)
address.state = "NSW"    (raw: "NSW", field_confidence: 0.95)
address.postcode = "2000"    (raw: "2000", field_confidence: 0.93)
address.country = "Australia"    (raw: "Australia", field_confidence: 0.92)
```

### Example 2 — source_record_id 234536
RAW
```
REGISTER_NAME: AFS Licence
AFS_LIC_NUM: 234536
AFS_LIC_NAME: MOVEBANK LTD
AFS_LIC_ABN_ACN: 91087651090
AFS_LIC_START_DT: 01/12/2003
AFS_LIC_PRE_FSR: 
AFS_LIC_ADD_LOCAL: BRISBANE
AFS_LIC_ADD_STATE: QLD
AFS_LIC_ADD_PCODE: 4000
AFS_LIC_ADD_COUNTRY: Australia
AFS_LIC_CONDITION: "This licence authorises the licensee to carry on a financial services
```
CANONICAL
```
entity.legal_name = "MOVEBANK LTD"    (raw: "MOVEBANK LTD", field_confidence: 0.93)
entity.abn = "91087651090"    (raw: "91087651090", field_confidence: 0.9)
address.locality = "BRISBANE"    (raw: "BRISBANE", field_confidence: 0.93)
address.state = "QLD"    (raw: "QLD", field_confidence: 0.95)
address.postcode = "4000"    (raw: "4000", field_confidence: 0.93)
address.country = "Australia"    (raw: "Australia", field_confidence: 0.92)
```

### Example 3 — source_record_id 227163
RAW
```
REGISTER_NAME: AFS Licence
AFS_LIC_NUM: 227163
AFS_LIC_NAME: JACANDA CAPITAL PTY. LIMITED
AFS_LIC_ABN_ACN: 14094254690
AFS_LIC_START_DT: 16/04/2003
AFS_LIC_PRE_FSR: "Securities dealer","000201897"
AFS_LIC_ADD_LOCAL: SYDNEY
AFS_LIC_ADD_STATE: NSW
AFS_LIC_ADD_PCODE: 2000
AFS_LIC_ADD_COUNTRY: Australia
AFS_LIC_CONDITION: "This licence authorises the licensee to carry on a financial services
```
CANONICAL
```
entity.legal_name = "JACANDA CAPITAL PTY. LIMITED"    (raw: "JACANDA CAPITAL PTY. LIMITED", field_confidence: 0.93)
entity.abn = "14094254690"    (raw: "14094254690", field_confidence: 0.9)
address.locality = "SYDNEY"    (raw: "SYDNEY", field_confidence: 0.93)
address.state = "NSW"    (raw: "NSW", field_confidence: 0.95)
address.postcode = "2000"    (raw: "2000", field_confidence: 0.93)
address.country = "Australia"    (raw: "Australia", field_confidence: 0.92)
```

### Example 4 — source_record_id 227675
RAW
```
REGISTER_NAME: AFS Licence
AFS_LIC_NUM: 227675
AFS_LIC_NAME: CHOICE PRIVATE CLIENTS PTY LTD
AFS_LIC_ABN_ACN: 46050199338
AFS_LIC_START_DT: 01/07/2003
AFS_LIC_PRE_FSR: 
AFS_LIC_ADD_LOCAL: SOUTH MELBOURNE
AFS_LIC_ADD_STATE: VIC
AFS_LIC_ADD_PCODE: 3205
AFS_LIC_ADD_COUNTRY: Australia
AFS_LIC_CONDITION: "This licence authorises the licensee to carry on a financial services
```
CANONICAL
```
entity.legal_name = "CHOICE PRIVATE CLIENTS PTY LTD"    (raw: "CHOICE PRIVATE CLIENTS PTY LTD", field_confidence: 0.93)
entity.abn = "46050199338"    (raw: "46050199338", field_confidence: 0.9)
address.locality = "SOUTH MELBOURNE"    (raw: "SOUTH MELBOURNE", field_confidence: 0.93)
address.state = "VIC"    (raw: "VIC", field_confidence: 0.95)
address.postcode = "3205"    (raw: "3205", field_confidence: 0.93)
address.country = "Australia"    (raw: "Australia", field_confidence: 0.92)
```

### Example 5 — source_record_id 235130
RAW
```
REGISTER_NAME: AFS Licence
AFS_LIC_NUM: 235130
AFS_LIC_NAME: BREEZE UNDERWRITING PTY LTD
AFS_LIC_ABN_ACN: 65003922487
AFS_LIC_START_DT: 23/09/2003
AFS_LIC_PRE_FSR: "General insurance broker","000020577"
AFS_LIC_ADD_LOCAL: EAST MELBOURNE
AFS_LIC_ADD_STATE: VIC
AFS_LIC_ADD_PCODE: 3002
AFS_LIC_ADD_COUNTRY: Australia
AFS_LIC_CONDITION: "This licence authorises the licensee to carry on a financial services
```
CANONICAL
```
entity.legal_name = "BREEZE UNDERWRITING PTY LTD"    (raw: "BREEZE UNDERWRITING PTY LTD", field_confidence: 0.93)
entity.abn = "65003922487"    (raw: "65003922487", field_confidence: 0.9)
address.locality = "EAST MELBOURNE"    (raw: "EAST MELBOURNE", field_confidence: 0.93)
address.state = "VIC"    (raw: "VIC", field_confidence: 0.95)
address.postcode = "3002"    (raw: "3002", field_confidence: 0.93)
address.country = "Australia"    (raw: "Australia", field_confidence: 0.92)
```

## Your decision

Run exactly one of:

    firm onboard asic-afs-licensee --decide "approve"
    firm onboard asic-afs-licensee --decide "reject: <what is wrong and what to use instead>"
    firm onboard asic-afs-licensee --decide "abandon"

You never edit the config directly — a hand-edited config is hand-authored, and
the point is that it is not. Reject with a comment instead.