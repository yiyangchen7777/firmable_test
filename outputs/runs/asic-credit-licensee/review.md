# Mapping review — asic-credit-licensee

| | |
|---|---|
| Dataset | asic-credit-licensee — ASIC – Credit Licensee Dataset |
| Publisher / licence | Australian Securities and Investments Commission (ASIC) / cc-by |
| Resource | https://data.gov.au/data/dataset/fa0b0d71-b8b8-4af8-bc59-0b000ce0d5e4/resource/35953a01-a9a8-4609-8566-c9fa7de465d3/download/credit_lic_202610.csv |
| Reader | {"format": "csv", "delimiter": ",", "encoding": "utf-8-sig", "header_row": 0, "sheet": null} |
| Agent run | revisions used 1/3 · steps 8 |
| **Status** | **PASSING WITH FLAGS** |
| Source reliability | 0.9 — ASIC is the national regulator and this is its own credit licence register, published under CC-BY, so licensee identity, licence and address claims are first-hand. |
| Record id | column ['CRED_LIC_NUM'] — CRED_LIC_NUM is ASIC's own licence key: 200 distinct values over 200 profiled rows and 0% null, so it is unique per record. CRED_LIC_ABN_ACN has only 194 distinct values (shared '0' placeholders and repeats), so it would fail uniqueness. |
| Observed at | dataset_modified → 2026-10-15 (basis: proxy) — No per-record extract or last-updated column exists. CRED_LIC_START_DT is the licence start date (valid_from material, and 2010-2011 dates for a weekly-refreshed register), so it is not an assertion date. Use dataset_modified as a weak proxy with basis 'proxy'. |

## Mapping (7 field mappings from 17 source columns)

| canonical | ← source column | transforms | conf. | cond. | evidence |
|---|---|---|---|---|---|
| entity.legal_name | CRED_LIC_NAME | `["trim", "empty_to_null"]` | 0.92 |  | CRED_LIC_NAME holds values such as 'SAVINGS PTY LTD', 'MACQUARIE BANK LIMITED' and 'BURL, DAMIEN'. These are the registered names of the licensee (companies, and individuals in surname-first form), 200 distinct over 200  |
| entity.abn | CRED_LIC_ABN_ACN | `["strip_float_suffix", "digits_only", {"keep_if_length": 11}, "abn_normalize"]` | 0.9 | yes | CRED_LIC_ABN_ACN is a mixed identifier column. 11-digit values such as '22105729100' and '48124489318' are ABNs, while 9-digit values such as '108398750' are ACNs. The 11-digit gate keeps ABNs only; other lengths such as |
| entity.acn | CRED_LIC_ABN_ACN | `["strip_float_suffix", "digits_only", {"keep_if_length": 9}, "acn_normalize"]` | 0.9 | yes | CRED_LIC_ABN_ACN holds 9-digit values such as '108398750' (FMW MORTGAGE SERVICES PTY LTD), which are ACNs. The 9-digit gate keeps only these and abstains on 11-digit ABNs, so the two mappings are complementary. |
| entity.trading_name | CRED_LIC_BN | `["trim", "empty_to_null"]` | 0.85 |  | CRED_LIC_BN ('BN' = business name) holds values such as 'FINANCEMYWAY' (licensee FMW MORTGAGE SERVICES PTY LTD) and 'TOP GEAR FINANCE' (licensee BURL, DAMIEN). These are names the licensee trades under, distinct from the |
| address.locality | CRED_LIC_LOCALITY | `["trim", "empty_to_null"]` | 0.85 |  | CRED_LIC_LOCALITY holds suburb/town names such as 'ERSKINE', 'UNDERWOOD' and 'MELBOURNE'. They are consistent with the paired state and postcode columns (ERSKINE/WA/6210), so this is the licensee's address locality. A sp |
| address.state | CRED_LIC_STATE | `["trim", "empty_to_null", "state_normalize"]` | 0.95 |  | CRED_LIC_STATE has 6 distinct abbreviations (WA, QLD, VIC, NSW, SA, TAS). They match the localities (ERSKINE is in WA, SYDNEY in NSW), so this is the address state. |
| address.postcode | CRED_LIC_PCODE | `["trim", "empty_to_null", "strip_float_suffix", "postcode_normalize"]` | 0.93 |  | CRED_LIC_PCODE holds 4-digit values such as '6210', '4119' and '3000'. They are consistent with the locality and state (MELBOURNE/VIC/3000), so this is the address postcode. postcode_normalize protects against lost leadi |

## Validation — 350 held-out rows (loop set; final acceptance runs once after approval)

| check | threshold | result | pass |
|---|---|---|---|
| identifier checksum (entity.abn) | >= 95% | 100.0% (318 ok / 0 failed) | ✅ |
| identifier checksum (entity.acn) | >= 95% | 100.0% (19 ok / 0 failed) | ✅ |
| enum legality (address.state) | >= 98% | 100.0% (350 ok / 0 failed) | ✅ |
| null drift (entity.legal_name ← CRED_LIC_NAME) | <= +2pp | +0.0% | ✅ |
| null drift (entity.trading_name ← CRED_LIC_BN) | <= +2pp | +0.0% | ✅ |
| null drift (address.locality ← CRED_LIC_LOCALITY) | <= +2pp | +0.0% | ✅ |
| null drift (address.state ← CRED_LIC_STATE) | <= +2pp | +0.0% | ✅ |
| null drift (address.postcode ← CRED_LIC_PCODE) | <= +2pp | +0.0% | ✅ |
| conditional pair coverage (CRED_LIC_ABN_ACN → entity.abn + entity.acn) | >= 95% of non-null | 96.3% | ✅ |
| record_id unique (full sample) | 0 duplicates | 0 duplicates | ✅ |
| minimum useful (a name or an identifier mapped) | required | yes | ✅ |

### Failing examples
- `entity.abn / entity.acn`: identifier_unclassified (no claim emitted) (raw: `0`)
- `entity.abn / entity.acn`: identifier_unclassified (no claim emitted) (raw: `94122871`)
- `entity.abn / entity.acn`: identifier_unclassified (no claim emitted) (raw: `0`)
- `entity.abn / entity.acn`: identifier_unclassified (no claim emitted) (raw: `0`)
- `entity.abn / entity.acn`: identifier_unclassified (no claim emitted) (raw: `0`)

## Semantic spot-check — 10 held-out records: 51 ok, 3 suspicious

| record | field | verdict | why |
|---|---|---|---|
| 382348 | entity.legal_name | ok | CRED_LIC_NAME 'JACKEEN PTY LTD' is the licensee's registered company name, and the BN column is empty. |
| 382348 | entity.abn | ok | 11-digit value in CRED_LIC_ABN_ACN for a company row; the checksum passes and nothing suggests it belongs to another party. |
| 382348 | address.locality | ok | MAUDSLAND is a suburb consistent with QLD 4210. |
| 382348 | address.state | ok | QLD matches the locality and postcode. |
| 382348 | address.postcode | ok | 4210 is consistent with Maudsland, QLD. |
| 385273 | entity.legal_name | ok | Individual licensee in surname-first form; the licensee's own name, not the brand. |
| 385273 | entity.abn | ok | 11-digit ABN with a valid checksum, on a row whose licensee is a sole individual, so it plausibly is the licensee's own ABN. |
| 385273 | entity.trading_name | ok | CRED_LIC_BN 'HOME LOAN MENTORS' is a business name distinct from the personal legal name. |
| 385273 | address.locality | ok | BALACLAVA is a suburb consistent with VIC 3183. |
| 385273 | address.state | ok | VIC matches the locality and postcode. |
| 385273 | address.postcode | ok | 3183 is consistent with Balaclava, VIC. |
| 385220 | entity.legal_name | ok | 'DRA GROUP PTY LTD' is a registered company name, and the BN column is empty. |
| 385220 | entity.abn | ok | 11-digit ABN on a company row, with nothing indicating a different party. |
| 385220 | address.locality | ok | MATRAVILLE is a suburb consistent with NSW 2036. |
| 385220 | address.state | ok | NSW matches the locality. |
| 385220 | address.postcode | ok | 2036 is consistent with Matraville, NSW. |
| 383889 | entity.legal_name | ok | Individual licensee name in surname-first form, which is the registered name. |
| 383889 | entity.abn | ok | 11-digit ABN on a sole-individual row; plausibly the licensee's own. |
| 383889 | entity.trading_name | ok | 'CROSS TAX & ACC. SERVICES' is a business name separate from the individual's legal name. |
| 383889 | address.locality | suspicious | 'KINGSWAY CARINGBAH' mixes a street name (The Kingsway) with the suburb Caringbah, so a street fragment has leaked into the locality field. |
| 383889 | address.state | ok | NSW is consistent with Caringbah and postcode 2229. |
| 383889 | address.postcode | ok | 2229 is the Caringbah postcode. |
| 376718 | entity.legal_name | ok | 'BIRCHCORP PTY. LTD.' is the licensee's registered company name. |
| 376718 | entity.abn | ok | 11-digit ABN on a company row; the nonzero AFSL number is a separate unmapped column and does not conflict. |
| 376718 | address.locality | ok | BAULKHAM HILLS is a suburb consistent with NSW 2153. |
| 376718 | address.state | ok | NSW matches the locality. |
| 376718 | address.postcode | ok | 2153 is the Baulkham Hills postcode. |
| 384679 | entity.legal_name | ok | 'REX GORELL FAMILY GROUP PTY LTD' is a company name with a PTY LTD suffix. |
| 384679 | entity.abn | ok | 11-digit ABN on a company row, with no sign of an agent's or parent's ABN. |
| 384679 | address.locality | ok | GEELONG is a city consistent with VIC 3220. |
| 384679 | address.state | ok | VIC matches Geelong. |
| 384679 | address.postcode | ok | 3220 is the Geelong postcode. |
| 385840 | entity.legal_name | ok | 'EQUIUS PTY LTD' is a registered company name, and the BN column is empty. |
| 385840 | entity.abn | ok | 11-digit ABN on a company row. |
| 385840 | address.locality | ok | CHARLESTOWN is a suburb consistent with NSW 2290. |
| 385840 | address.state | ok | NSW matches the locality. |
| 385840 | address.postcode | ok | 2290 is consistent with Charlestown, NSW. |
| 364322 | entity.legal_name | ok | 'CADANSE HOLDINGS PTY LTD' is the registered company name; the brand sits in BN. |
| 364322 | entity.abn | ok | 11-digit ABN on a company row. |
| 364322 | entity.trading_name | ok | 'ELITE BROKERAGE SERVICES' is a trading style distinct from the registered name. |
| 364322 | address.locality | ok | THORNLIE is a suburb consistent with WA 6108. |
| 364322 | address.state | ok | WA matches the locality. |
| 364322 | address.postcode | ok | 6108 is the Thornlie postcode. |
| 377517 | entity.legal_name | ok | 'VAULT MORTGAGE CORPORATION PTY LTD' is a registered company name. |
| 377517 | entity.abn | ok | 11-digit ABN on a company row. |
| 377517 | address.locality | ok | DRUMMOYNE is a suburb consistent with NSW 2047. |
| 377517 | address.state | ok | NSW matches the locality. |
| 377517 | address.postcode | ok | 2047 is the Drummoyne postcode. |
| 385338 | entity.legal_name | suspicious | 'TRUSTEES OF HELYER FAMILY TRUST' names the trust and its trustees rather than a registered legal entity, so it may be a party-confusion case; the actual licens |
| 385338 | entity.acn | suspicious | A trust is not a company and has no ACN, so this 9-digit value probably belongs to the corporate trustee, not the entity named in legal_name; the ownership mism |
| 385338 | entity.trading_name | ok | 'MASTERPLAN HOME LOANS' in the BN column is a trading brand, not a legal name. |
| 385338 | address.locality | ok | PARKINSON is a suburb consistent with QLD 4115. |
| 385338 | address.state | ok | QLD matches the locality and postcode. |
| 385338 | address.postcode | ok | 4115 is consistent with Parkinson, QLD. |

Notes: CRED_LIC_NAME can hold trust or trustee names (e.g. 'TRUSTEES OF HELYER FAMILY TRUST'), and the identifier on those rows may belong to a trustee company rather than the named subject. Consider conditional handling or entity_type awareness.; CRED_LIC_LOCALITY is contaminated with street text ('KINGSWAY CARINGBAH'). The earlier reviewer acceptance does not make the value a clean locality, so it still needs a cleanup rule or a flag.; The shared ABN/ACN column is gated by length only, and the ABN checksum is not confirmed in the transform chain; the two ABNs checked by hand (46108175024, 66305781849) pass.; Individual licensees (surname-first names) carry ABNs and have trading names in BN; no entity_type was inferred, which is appropriate. CRED_LIC_STATUS ('APPR') and the start date were not mapped, which is correct since they describe the licence.

## Unmapped columns (11)

| source column | reason |
|---|---|
| REGISTER_NAME | Constant 'Credit Licence' for every row (1 distinct value); names the register, not an entity attribute. |
| CRED_LIC_NUM | Licence number: used as record_id (the source's own record key, 200 distinct over 200 rows). It is a record identifier, not an entity identifier, and has no ontology field. |
| CRED_LIC_START_DT | dd/mm/yyyy licence start date (e.g. '04/11/2010'). It is when the licence was granted, not entity.date_registered (the company's registration date), and is not a record observation date; valid_from material only. |
| CRED_LIC_END_DT | 100% null in the profile; there is nothing to map. |
| CRED_LIC_AFSL_NUM | Australian Financial Services Licence number ('0' when none, otherwise often equal to the credit licence number). It is a licence identifier with no ontology field, not an ABN/ACN. |
| CRED_LIC_STATUS_HISTORY | 99.5% null free text about past suspensions (e.g. 'Suspended at the request of Licensee/Registrant 18/07/2018 1'); no ontology field. |
| CRED_LIC_LAT | Geocoded latitude; the ontology has no coordinate field. |
| CRED_LIC_LNG | Geocoded longitude; the ontology has no coordinate field. |
| CRED_LIC_EDRS | External dispute resolution scheme memberships (AFCA, COSL, FOS; '~'-separated); a relationship to other bodies with no ontology field. |
| CRED_LIC_AUTHORISATIONS | Free-text description of licence authorisations; no ontology field. |
| CRED_LIC_STATUS | Values such as 'APPR' describe the approval status of the credit licence, not the company's existence or registration status, so it does not map to entity.status. Unmapped per human reviewer. |

## Side-by-side — 5 raw records vs their canonical observations

Read these for meaning, not parse success: is the date a registration date or a
licence date? Is the name the licensee or the applicant? Is the ABN the subject
entity's?

### Example 1 — source_record_id 383131
RAW
```
REGISTER_NAME: Credit Licence
CRED_LIC_NUM: 383131
CRED_LIC_NAME: NATIONAL FINANCIAL SERVICES PTY LTD
CRED_LIC_START_DT: 09/12/2010
CRED_LIC_END_DT: 
CRED_LIC_STATUS: APPR
CRED_LIC_ABN_ACN: 79001827005
CRED_LIC_AFSL_NUM: 383131
CRED_LIC_STATUS_HISTORY: 
CRED_LIC_LOCALITY: KINGSTON
CRED_LIC_STATE: ACT
CRED_LIC_PCODE: 2604
CRED_LIC_LAT: -35.3152303
CRED_LIC_LNG: 149.1465925
CRED_LIC_EDRS: AFCA
CRED_LIC_BN: 
CRED_LIC_AUTHORISATIONS: This licence authorises the licensee to:~Engage in credit activities o
```
CANONICAL
```
entity.legal_name = "NATIONAL FINANCIAL SERVICES PTY LTD"    (raw: "NATIONAL FINANCIAL SERVICES PTY LTD", field_confidence: 0.92)
entity.abn = "79001827005"    (raw: "79001827005", field_confidence: 0.9)
address.locality = "KINGSTON"    (raw: "KINGSTON", field_confidence: 0.85)
address.state = "ACT"    (raw: "ACT", field_confidence: 0.95)
address.postcode = "2604"    (raw: "2604", field_confidence: 0.93)
```

### Example 2 — source_record_id 383024
RAW
```
REGISTER_NAME: Credit Licence
CRED_LIC_NUM: 383024
CRED_LIC_NAME: LOCKLEY, RICHARD ALLAN
CRED_LIC_START_DT: 19/10/2010
CRED_LIC_END_DT: 
CRED_LIC_STATUS: APPR
CRED_LIC_ABN_ACN: 69703468233
CRED_LIC_AFSL_NUM: 0
CRED_LIC_STATUS_HISTORY: 
CRED_LIC_LOCALITY: CONNOLLY
CRED_LIC_STATE: WA
CRED_LIC_PCODE: 6027
CRED_LIC_LAT: -31.747944
CRED_LIC_LNG: 115.7497916
CRED_LIC_EDRS: AFCA
CRED_LIC_BN: INTEGRITY CAPITAL
CRED_LIC_AUTHORISATIONS: This licence authorises the licensee to:~Engage in credit activities o
```
CANONICAL
```
entity.legal_name = "LOCKLEY, RICHARD ALLAN"    (raw: "LOCKLEY, RICHARD ALLAN", field_confidence: 0.92)
entity.abn = "69703468233"    (raw: "69703468233", field_confidence: 0.9)
entity.trading_name = "INTEGRITY CAPITAL"    (raw: "INTEGRITY CAPITAL", field_confidence: 0.85)
address.locality = "CONNOLLY"    (raw: "CONNOLLY", field_confidence: 0.85)
address.state = "WA"    (raw: "WA", field_confidence: 0.95)
address.postcode = "6027"    (raw: "6027", field_confidence: 0.93)
```

### Example 3 — source_record_id 288421
RAW
```
REGISTER_NAME: Credit Licence
CRED_LIC_NUM: 288421
CRED_LIC_NAME: LIFESTYLE ASSET MANAGEMENT PTY LTD
CRED_LIC_START_DT: 25/10/2010
CRED_LIC_END_DT: 
CRED_LIC_STATUS: APPR
CRED_LIC_ABN_ACN: 58113067968
CRED_LIC_AFSL_NUM: 288421
CRED_LIC_STATUS_HISTORY: 
CRED_LIC_LOCALITY: BARANGAROO
CRED_LIC_STATE: NSW
CRED_LIC_PCODE: 2000
CRED_LIC_LAT: -33.8614084
CRED_LIC_LNG: 151.2016877
CRED_LIC_EDRS: AFCA
CRED_LIC_BN: 
CRED_LIC_AUTHORISATIONS: This licence authorises the licensee to:~Engage in credit activities o
```
CANONICAL
```
entity.legal_name = "LIFESTYLE ASSET MANAGEMENT PTY LTD"    (raw: "LIFESTYLE ASSET MANAGEMENT PTY LTD", field_confidence: 0.92)
entity.abn = "58113067968"    (raw: "58113067968", field_confidence: 0.9)
address.locality = "BARANGAROO"    (raw: "BARANGAROO", field_confidence: 0.85)
address.state = "NSW"    (raw: "NSW", field_confidence: 0.95)
address.postcode = "2000"    (raw: "2000", field_confidence: 0.93)
```

### Example 4 — source_record_id 314889
RAW
```
REGISTER_NAME: Credit Licence
CRED_LIC_NUM: 314889
CRED_LIC_NAME: 5 WEALTH MANAGEMENT PTY LTD
CRED_LIC_START_DT: 01/12/2010
CRED_LIC_END_DT: 
CRED_LIC_STATUS: APPR
CRED_LIC_ABN_ACN: 50003640097
CRED_LIC_AFSL_NUM: 314889
CRED_LIC_STATUS_HISTORY: 
CRED_LIC_LOCALITY: RHODES
CRED_LIC_STATE: NSW
CRED_LIC_PCODE: 2138
CRED_LIC_LAT: -33.8290589
CRED_LIC_LNG: 151.0873578
CRED_LIC_EDRS: AFCA
CRED_LIC_BN: 
CRED_LIC_AUTHORISATIONS: This licence authorises the licensee to:~Engage in credit activities o
```
CANONICAL
```
entity.legal_name = "5 WEALTH MANAGEMENT PTY LTD"    (raw: "5 WEALTH MANAGEMENT PTY LTD", field_confidence: 0.92)
entity.abn = "50003640097"    (raw: "50003640097", field_confidence: 0.9)
address.locality = "RHODES"    (raw: "RHODES", field_confidence: 0.85)
address.state = "NSW"    (raw: "NSW", field_confidence: 0.95)
address.postcode = "2138"    (raw: "2138", field_confidence: 0.93)
```

### Example 5 — source_record_id 383982
RAW
```
REGISTER_NAME: Credit Licence
CRED_LIC_NUM: 383982
CRED_LIC_NAME: FUTURE HOLIDAY FINANCE PTY LTD
CRED_LIC_START_DT: 23/12/2010
CRED_LIC_END_DT: 
CRED_LIC_STATUS: APPR
CRED_LIC_ABN_ACN: 61108475298
CRED_LIC_AFSL_NUM: 0
CRED_LIC_STATUS_HISTORY: 
CRED_LIC_LOCALITY: VARSITY LAKES
CRED_LIC_STATE: QLD
CRED_LIC_PCODE: 4227
CRED_LIC_LAT: -28.0971316
CRED_LIC_LNG: 153.3992325
CRED_LIC_EDRS: AFCA
CRED_LIC_BN: 
CRED_LIC_AUTHORISATIONS: This licence authorises the licensee to:~Engage in credit activities a
```
CANONICAL
```
entity.legal_name = "FUTURE HOLIDAY FINANCE PTY LTD"    (raw: "FUTURE HOLIDAY FINANCE PTY LTD", field_confidence: 0.92)
entity.abn = "61108475298"    (raw: "61108475298", field_confidence: 0.9)
address.locality = "VARSITY LAKES"    (raw: "VARSITY LAKES", field_confidence: 0.85)
address.state = "QLD"    (raw: "QLD", field_confidence: 0.95)
address.postcode = "4227"    (raw: "4227", field_confidence: 0.93)
```

## Your decision

Run exactly one of:

    firm onboard asic-credit-licensee --decide "approve"
    firm onboard asic-credit-licensee --decide "reject: <what is wrong and what to use instead>"
    firm onboard asic-credit-licensee --decide "abandon"

You never edit the config directly — a hand-edited config is hand-authored, and
the point is that it is not. Reject with a comment instead.