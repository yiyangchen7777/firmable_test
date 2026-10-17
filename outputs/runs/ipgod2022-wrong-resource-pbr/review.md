# Mapping review — ipgod2022

| | |
|---|---|
| Dataset | ipgod2022 — IPGOD2022 |
| Publisher / licence | IP Australia / cc-by-2.5 |
| Resource | https://data.gov.au/data/dataset/49017fd0-e7be-4fc0-88c8-046fc366d980/resource/952d7cf9-8412-4205-80de-405a725a2017/download/pbr-application.csv |
| Reader | {"format": "csv", "delimiter": ",", "encoding": "utf-8-sig", "header_row": 0, "sheet": null} |
| Agent run | revisions used 3/3 · steps 11 |
| **Status** | **NOT USEFUL** |
| Source reliability | 0.9 — IP Australia is the national regulator publishing its own administrative register under CC-BY 2.5, but this extract carries no entity-level claims. |
| Record id | column ['application_number'] — application_number is the source's own PBR application key and has 200 distinct values over 200 profiled rows, so it is unique per record. There are no entity identifiers in the extract, so the key cannot be an ABN anyway. |
| Observed at | dataset_modified → 2022-06-20 (basis: proxy) — No per-record extract or snapshot date column exists. All date columns are IP lifecycle events (filing, priority, registration, enforceable, retired), which are valid_from-type facts and not assertion times. Falling back to the catalogue modified date (2022-06-20) as a weak proxy. |

## Mapping (0 field mappings from 10 source columns)

| canonical | ← source column | transforms | conf. | cond. | evidence |
|---|---|---|---|---|---|


## Validation — 350 held-out rows (loop set; final acceptance runs once after approval)

| check | threshold | result | pass |
|---|---|---|---|
| record_id unique (full sample) | 0 duplicates | 0 duplicates | ✅ |
| minimum useful (a name or an identifier mapped) | required | NO | ❌ |

### Failing examples
none

## Semantic spot-check — 10 held-out records: 0 ok, 0 suspicious

| record | field | verdict | why |
|---|---|---|---|


Notes: The config has an empty fields[] and produced no canonical claims for any of the 10 records, so there is nothing to mark ok or suspicious.; The raw records are plant breeder's rights (PBR) IP records. They contain only application number, right type, status and date columns. None of them has a party name, ABN/ACN, address or website.; The ontology fields are entity and address attributes. None of them maps cleanly to these columns, so an empty mapping may be correct for this source.; If a later revision maps any of these columns, it needs close review. status (terminated/withdrawn) describes the IP right, not the entity, so it must not go to entity.status. The filed, registration, enforceable and retired dates are IP-right lifecycle dates, not entity.date_registered.; The pipeline should check that this source is meant to feed the entity ontology at all. A mapping that yields zero claims across every record may point to a wrong source or an incomplete config.

## Unmapped columns (10)

| source column | reason |
|---|---|
| ip_right_type | Single constant value 'pbr' (plant breeder's rights); describes the type of IP right, not an entity attribute. No ontology field. |
| application_number | Identifier of the PBR application (e.g. '1991/079'), not an ABN/ACN/NZBN. Used as record_id only; no entity identifier field. |
| ip_right_sub_type | Constant 'pbr', duplicating ip_right_type; IP-right classification, no ontology field. |
| status | Values (terminated, expired, withdrawn, refused, granted) are the lifecycle status of the IP application/right, not of a legal entity. Mapping to entity.status would be semantically wrong, so it is left unmapped. |
| earliest_filed_date | Date the IP application was first filed (e.g. 1991-08-28), not an entity registration date. Not entity.date_registered. |
| priority_date | IP priority date, identical to the filing date in the samples; an attribute of the application, not an entity registration date. |
| gained_registration_status_date | Date the IP right gained registered status (26.5% null); a right-level event, not entity registration. No ontology field. |
| gained_enforceable_status_date | Date the IP right became enforceable; mirrors gained_registration_status_date. A right-level event, no ontology field. |
| enforceable_from_date | Date from which the IP right is enforceable, equal to the filing date in the samples; right-level, not entity registration. |
| deemed_retired_date | Date the IP right was deemed retired (e.g. 1996-01-05); not an entity deregistration or registration date. No ontology field. |

## Side-by-side — 5 raw records vs their canonical observations

Read these for meaning, not parse success: is the date a registration date or a
licence date? Is the name the licensee or the applicant? Is the ABN the subject
entity's?

### Example 1 — source_record_id 1992/008
RAW
```
ip_right_type: pbr
application_number: 1992/008
ip_right_sub_type: pbr
status: terminated
earliest_filed_date: 1992-02-03 00:00:00.000
priority_date: 1992-02-03 00:00:00.000
gained_registration_status_date: 1993-09-22 00:00:00.000
gained_enforceable_status_date: 1993-09-22 00:00:00.000
enforceable_from_date: 1992-02-03 00:00:00.000
deemed_retired_date: 1995-05-24 00:00:00.000
```
CANONICAL
```
(no claims)
```

### Example 2 — source_record_id 1991/128
RAW
```
ip_right_type: pbr
application_number: 1991/128
ip_right_sub_type: pbr
status: terminated
earliest_filed_date: 1991-12-16 00:00:00.000
priority_date: 1991-12-16 00:00:00.000
gained_registration_status_date: 1993-01-19 00:00:00.000
gained_enforceable_status_date: 1993-01-19 00:00:00.000
enforceable_from_date: 1991-12-16 00:00:00.000
deemed_retired_date: 1997-01-14 00:00:00.000
```
CANONICAL
```
(no claims)
```

### Example 3 — source_record_id 1989/103
RAW
```
ip_right_type: pbr
application_number: 1989/103
ip_right_sub_type: pbr
status: terminated
earliest_filed_date: 1989-11-23 00:00:00.000
priority_date: 1989-11-23 00:00:00.000
gained_registration_status_date: 1991-10-04 00:00:00.000
gained_enforceable_status_date: 1991-10-04 00:00:00.000
enforceable_from_date: 1989-11-23 00:00:00.000
deemed_retired_date: 2002-07-31 00:00:00.000
```
CANONICAL
```
(no claims)
```

### Example 4 — source_record_id 1989/120
RAW
```
ip_right_type: pbr
application_number: 1989/120
ip_right_sub_type: pbr
status: terminated
earliest_filed_date: 1989-11-23 00:00:00.000
priority_date: 1989-11-23 00:00:00.000
gained_registration_status_date: 1999-06-02 00:00:00.000
gained_enforceable_status_date: 1999-06-02 00:00:00.000
enforceable_from_date: 1989-11-23 00:00:00.000
deemed_retired_date: 2000-05-22 00:00:00.000
```
CANONICAL
```
(no claims)
```

### Example 5 — source_record_id 1992/046
RAW
```
ip_right_type: pbr
application_number: 1992/046
ip_right_sub_type: pbr
status: terminated
earliest_filed_date: 1992-04-07 00:00:00.000
priority_date: 1992-04-07 00:00:00.000
gained_registration_status_date: 1993-01-11 00:00:00.000
gained_enforceable_status_date: 1993-01-11 00:00:00.000
enforceable_from_date: 1992-04-07 00:00:00.000
deemed_retired_date: 1998-03-12 00:00:00.000
```
CANONICAL
```
(no claims)
```

## Your decision

Run exactly one of:

    firm onboard ipgod2022 --decide "approve"
    firm onboard ipgod2022 --decide "reject: <what is wrong and what to use instead>"
    firm onboard ipgod2022 --decide "abandon"

You never edit the config directly — a hand-edited config is hand-authored, and
the point is that it is not. Reject with a comment instead.