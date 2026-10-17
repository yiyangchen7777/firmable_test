# Mapping review — ipgod2022

| | |
|---|---|
| Dataset | ipgod2022 — IPGOD2022 |
| Publisher / licence | IP Australia / cc-by-2.5 |
| Resource | https://data.gov.au/data/dataset/49017fd0-e7be-4fc0-88c8-046fc366d980/resource/89dacae9-4649-4612-aeb8-489af3aec379/download/design-party-activity.csv |
| Reader | {"format": "csv", "delimiter": ",", "encoding": "utf-8-sig", "header_row": 0, "sheet": null} |
| Agent run | revisions used 3/3 · steps 11 |
| **Status** | **NOT PASSING** |
| Source reliability | 0.8 — IP Australia is the national regulator for IP rights, but party names, addresses and ABNs are applicant-supplied (and individuals are pseudonymised), so reliability sits below a core registry like ASIC or the ABR. |
| Record id | row_hash ['application_number', 'party_id', 'party_role', 'party_role_category', 'party_name', 'party_type', 'abn', 'state_code', 'post_code', 'country_code', 'effective_from_date', 'effective_to_date', 'is_current', 'is_founding'] — The table has one row per party-role-per-application event. application_number has 83 distinct values and party_id 68 in 200 rows, and the same party recurs across applications and roles, so neither is unique. There is no source record key, so row_hash over the whole row is the safe unique choice. |
| Observed at | dataset_modified → 2022-06-20 (basis: proxy) — There is no per-record extract or snapshot date. effective_from_date and effective_to_date describe when the party's role began or ended, which is valid_from material, not when the source asserted the record. So the catalogue modified date (2022-06-20) is used as a weak proxy. |

## Mapping (5 field mappings from 15 source columns)

| canonical | ← source column | transforms | conf. | cond. | evidence |
|---|---|---|---|---|---|
| entity.legal_name | party_name | `["trim", "empty_to_null"]` | 0.65 |  | Column party_name holds names such as 'davis ip pty ltd', 'exlites pty ltd', 'oculus vr llc'. Semantic spot-checks flagged that many rows are agent, opponent or submitter parties (e.g. opposition_claimant_agent 'krouzer  |
| entity.abn | abn | `["trim", "empty_to_null", "strip_float_suffix", "abn_normalize"]` | 0.8 |  | Column abn holds float-serialised 11-digit values such as '53637813471.0' and '35026846389.0'. Checksum pass is 100% (236/236). Semantic flags note that the ABN often sits on agent or submitter rows, so it identifies the |
| address.state | state_code | `["trim", "empty_to_null", "state_normalize"]` | 0.9 |  | Column state_code holds lowercase Australian state abbreviations ('qld', 'vic', 'nsw', 'wa', 'act', 'sa'), which state_normalize handles case-insensitively. Enum legality is 100%. It is the party's address state, not the |
| address.postcode | post_code | `["trim", "empty_to_null"]` | 0.65 |  | Column post_code mixes Australian 4-digit postcodes ('4006', '3000', padded ' 2075 ') with foreign postal codes ('qc, h4t 1k', '443-742', '90404', '315010', '95014'). The keep_if_length 4 gate turned about 15% of non-nul |
| address.country | country_code | `["trim", "empty_to_null"]` | 0.85 |  | Column country_code holds lowercase ISO-style codes ('au', 'vg', 'us', 'de', 'jp') sitting alongside the party's state and postcode, so it is the party's address country. It is not the IP right's filing country. Values a |

## Validation — 350 held-out rows (loop set; final acceptance runs once after approval)

| check | threshold | result | pass |
|---|---|---|---|
| identifier checksum (entity.abn) | >= 95% | 100.0% (236 ok / 0 failed) | ✅ |
| enum legality (address.state) | >= 98% | 100.0% (242 ok / 0 failed) | ✅ |
| null drift (entity.legal_name ← party_name) | <= +2pp | +0.0% | ✅ |
| null drift (entity.abn ← abn) | <= +2pp | +0.0% | ✅ |
| null drift (address.state ← state_code) | <= +2pp | +0.0% | ✅ |
| null drift (address.postcode ← post_code) | <= +2pp | +0.0% | ✅ |
| null drift (address.country ← country_code) | <= +2pp | -0.0% | ✅ |
| record_id effectively unique (full sample) | <= 0.5% duplicates | 6 duplicates (1.71%) | ❌ |
| minimum useful (a name or an identifier mapped) | required | yes | ✅ |

### Failing examples
none

## Semantic spot-check — 10 held-out records: 24 ok, 14 suspicious

| record | field | verdict | why |
|---|---|---|---|
| efded41ac8d5de0b | entity.legal_name | suspicious | party_role is opposition_claimant_agent, so this is the agent party (and a 'the trustee for ...' trust-style name), not the right holder; the config has no role |
| efded41ac8d5de0b | entity.abn | suspicious | The ABN sits on an opposition agent row, so it may belong to the agent or trustee rather than the IP right holder. |
| efded41ac8d5de0b | address.state | ok | nsw maps to NSW and matches the party's own address on this row. |
| efded41ac8d5de0b | address.postcode | suspicious | 1230 is a 1xxx PO-box-style postcode that is inconsistent with state NSW street addressing, so it may be a postal rather than physical address. |
| efded41ac8d5de0b | address.country | ok | au is the party's address country, but it is left lowercase and un-normalised. |
| 91fbf2960d85d10f | entity.legal_name | ok | Applicant/owner organisation 'apple inc' is the right holder and a plausible registered name. |
| 91fbf2960d85d10f | address.country | ok | us is the owner's country, consistent with a US company, though it is lowercase and not normalised. |
| d5c37838c9d51cc5 | entity.legal_name | suspicious | Role is opposition_claimant_agent, so 'krouzer ip' is an agent firm and also looks like a trading name, not the right holder's legal name. |
| d5c37838c9d51cc5 | entity.abn | suspicious | The ABN is on an agent row and may identify the agent firm rather than the right holder. |
| d5c37838c9d51cc5 | address.state | ok | nsw maps to NSW and is consistent with postcode 2153. |
| d5c37838c9d51cc5 | address.postcode | ok | 2153 is a valid NSW postcode consistent with the state, though it is the agent's address. |
| d5c37838c9d51cc5 | address.country | ok | au is consistent with the NSW state and postcode. |
| 545180385f435890 | entity.legal_name | suspicious | Role is applicant_agent, so 'davis ip pty ltd' is the applicant's agent rather than the right holder. |
| 545180385f435890 | entity.abn | suspicious | The ABN is on an agent row, so it identifies the agent, not the applicant or owner. |
| 545180385f435890 | address.state | ok | qld maps to QLD and is consistent with postcode 4006, though it is the agent's address. |
| 545180385f435890 | address.postcode | ok | 4006 is a valid QLD postcode consistent with the state. |
| 545180385f435890 | address.country | ok | au is consistent with the QLD state and postcode. |
| 5bc387c2506ddab4 | entity.legal_name | ok | Applicant/owner organisation with a Pty Ltd name is a plausible registered legal name. |
| 5bc387c2506ddab4 | entity.abn | ok | The ABN is on the owner's own row and aligned with the company name. |
| 5bc387c2506ddab4 | address.state | ok | nsw maps to NSW and is consistent with postcode 2010. |
| 5bc387c2506ddab4 | address.postcode | ok | Trimmed 2010 is a valid NSW postcode. |
| 5bc387c2506ddab4 | address.country | ok | au is consistent with the NSW address. |
| 5d8f9a0fa4e5a98f | entity.legal_name | ok | Opposition claimant 'apple inc' is a real party with its own name, though not the right holder of this design. |
| 5d8f9a0fa4e5a98f | address.postcode | ok | 95014 is a US ZIP (Cupertino), consistent with country us, kept as raw text. |
| 5d8f9a0fa4e5a98f | address.country | ok | us is consistent with the US ZIP and the empty state. |
| 8ea7ef015b3a04e2 | entity.legal_name | suspicious | Role is opposition_claimant_agent, so this is a patent attorney firm, not the right holder. |
| 8ea7ef015b3a04e2 | entity.abn | suspicious | The ABN is on an agent row and identifies the attorney firm, not the right holder. |
| 1d09b146826a7efd | entity.legal_name | suspicious | Role is opposition_claimant_agent, so 'herbert smith freehills' is a law firm acting as agent, and the name lacks a legal-entity suffix. |
| 1d09b146826a7efd | entity.abn | suspicious | The ABN is on an agent row and likely belongs to the law firm or partnership, not the right holder. |
| 7cee5440979393d7 | entity.legal_name | suspicious | Role is 'submitter' (category other), and 'banki haddock fiora' is a law/IP firm, not the right holder. |
| 7cee5440979393d7 | entity.abn | suspicious | The ABN is on a submitter row and identifies the submitting firm, not the right holder. |
| 7cee5440979393d7 | address.state | ok | nsw maps to NSW and is consistent with postcode 2000, though it is the submitter's address. |
| 7cee5440979393d7 | address.postcode | ok | 2000 is a valid NSW postcode consistent with the state. |
| 7cee5440979393d7 | address.country | ok | au is consistent with the NSW address. |
| bc4a750aa9d5fb54 | entity.legal_name | suspicious | party_name 'i244880' is a pseudonymised individual id, not a real name, so it is a junk legal_name claim. |
| bc4a750aa9d5fb54 | address.state | ok | qld maps to QLD and is consistent with postcode 4218. |
| bc4a750aa9d5fb54 | address.postcode | ok | Trimmed 4218 is a valid QLD postcode. |
| bc4a750aa9d5fb54 | address.country | ok | au is consistent with the QLD address. |

Notes: entity.legal_name is mapped from party_name with no filter on party_role or party_role_category, so agent, opponent and submitter parties become legal_name claims alongside right holders. The role columns are unmapped.; Several ABNs sit on agent or submitter rows (krouzer ip, davis ip, fpa, herbert smith freehills, banki haddock fiora), so they identify the agent firm rather than the right holder.; party_type=individual rows give pseudonymised ids as legal_name, which are junk values.; address.country is emitted as lowercase ISO codes (au, us) with no normalisation, and 1xxx PO-box-style postcodes are paired with state NSW.

## Unmapped columns (10)

| source column | reason |
|---|---|
| ip_right_type | Constant 'design' (1 distinct value); describes the IP right type, no ontology field. |
| application_number | 9-digit IP application identifier (e.g. 201914700), not an ACN despite the ACN-like hint; no ontology field. |
| party_id | Source-internal party identifier (e.g. 'o196099'), no ontology field. |
| party_role_category | Role of the party in the IP application (applicant, agent, opposition); relationship, not an entity attribute. |
| party_role | Role of the party in the IP application (owner, agent, opponent); relationship, not an entity attribute. |
| party_type | organisation/individual does not map to the entity_type enum (company, trust, etc.); guessing would risk harm. |
| effective_from_date | Start of the party's role on the IP record, not the entity's registration date, so not date_registered; also not a record-level extract date, so not observed_at. |
| effective_to_date | End of the party's role on the IP record (83% null); no ontology field. |
| is_current | Whether the party-role link is current, not the entity's status; no ontology field. |
| is_founding | Flag on the IP record history; no ontology field. |

## Side-by-side — 5 raw records vs their canonical observations

Read these for meaning, not parse success: is the date a registration date or a
licence date? Is the name the licensee or the applicant? Is the ABN the subject
entity's?

### Example 1 — source_record_id 0a903f1e5dbc055b
RAW
```
ip_right_type: design
application_number: 201914691
party_id: o161173
party_role_category: opposition
party_role: opposition_respondent
party_type: organisation
party_name: clipex ip limited
state_code: 
post_code: 
country_code: vg
effective_from_date: 2020-06-26 00:00:00.000
effective_to_date: 
is_current: True
abn: 
is_founding: True
```
CANONICAL
```
entity.legal_name = "clipex ip limited"    (raw: "clipex ip limited", field_confidence: 0.65)
address.country = "vg"    (raw: "vg", field_confidence: 0.85)
```

### Example 2 — source_record_id 2c462ff3917aeef2
RAW
```
ip_right_type: design
application_number: 201914693
party_id: o862063
party_role_category: opposition
party_role: opposition_claimant
party_type: organisation
party_name: griffith hack
state_code: vic
post_code: 3000
country_code: au
effective_from_date: 2020-06-26 00:00:00.000
effective_to_date: 
is_current: True
abn: 35026846389.0
is_founding: True
```
CANONICAL
```
entity.legal_name = "griffith hack"    (raw: "griffith hack", field_confidence: 0.65)
entity.abn = "35026846389"    (raw: "35026846389.0", field_confidence: 0.8)
address.state = "VIC"    (raw: "vic", field_confidence: 0.9)
address.postcode = "3000"    (raw: "3000", field_confidence: 0.65)
address.country = "au"    (raw: "au", field_confidence: 0.85)
```

### Example 3 — source_record_id a932bec1474b1e6b
RAW
```
ip_right_type: design
application_number: 200914770
party_id: i244880
party_role_category: applicant
party_role: owner
party_type: individual
party_name: i244880
state_code: qld
post_code:  4218 
country_code: au
effective_from_date: 2009-12-07 00:00:00.000
effective_to_date: 
is_current: True
abn: 
is_founding: True
```
CANONICAL
```
entity.legal_name = "i244880"    (raw: "i244880", field_confidence: 0.65)
address.state = "QLD"    (raw: "qld", field_confidence: 0.9)
address.postcode = "4218"    (raw: " 4218 ", field_confidence: 0.65)
address.country = "au"    (raw: "au", field_confidence: 0.85)
```

### Example 4 — source_record_id b198ea7c26c74749
RAW
```
ip_right_type: design
application_number: 201914701
party_id: o704372
party_role_category: applicant_agent
party_role: agent
party_type: organisation
party_name: spruson & ferguson
state_code: nsw
post_code: 2001
country_code: au
effective_from_date: 2019-08-20 00:00:00.000
effective_to_date: 2020-04-23 00:00:00.000
is_current: False
abn: 84362252431.0
is_founding: True
```
CANONICAL
```
entity.legal_name = "spruson & ferguson"    (raw: "spruson & ferguson", field_confidence: 0.65)
entity.abn = "84362252431"    (raw: "84362252431.0", field_confidence: 0.8)
address.state = "NSW"    (raw: "nsw", field_confidence: 0.9)
address.postcode = "2001"    (raw: "2001", field_confidence: 0.65)
address.country = "au"    (raw: "au", field_confidence: 0.85)
```

### Example 5 — source_record_id edc2e14af96322a2
RAW
```
ip_right_type: design
application_number: 201914694
party_id: o196099
party_role_category: opposition_agent
party_role: opposition_respondent_agent
party_type: organisation
party_name: davis ip pty ltd
state_code: qld
post_code: 4006
country_code: au
effective_from_date: 2020-06-26 00:00:00.000
effective_to_date: 
is_current: True
abn: 53637813471.0
is_founding: True
```
CANONICAL
```
entity.legal_name = "davis ip pty ltd"    (raw: "davis ip pty ltd", field_confidence: 0.65)
entity.abn = "53637813471"    (raw: "53637813471.0", field_confidence: 0.8)
address.state = "QLD"    (raw: "qld", field_confidence: 0.9)
address.postcode = "4006"    (raw: "4006", field_confidence: 0.65)
address.country = "au"    (raw: "au", field_confidence: 0.85)
```

## Your decision

Run exactly one of:

    firm onboard ipgod2022 --decide "approve"
    firm onboard ipgod2022 --decide "reject: <what is wrong and what to use instead>"
    firm onboard ipgod2022 --decide "abandon"

You never edit the config directly — a hand-edited config is hand-authored, and
the point is that it is not. Reject with a comment instead.