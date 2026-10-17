# Mapping review — acnc-register

| | |
|---|---|
| Dataset | acnc-register — ACNC Registered Charities |
| Publisher / licence | Australian Charities and Not-for-profits Commission (ACNC) / cc-by |
| Resource | https://data.gov.au/data/dataset/b050b242-4487-4306-abf5-07ca073e5594/resource/8fb32972-24e9-4c95-885e-7140be51be8a/download/datadotgov_main.csv |
| Reader | {"format": "csv", "delimiter": ",", "encoding": "utf-8-sig", "header_row": 0, "sheet": null} |
| Agent run | revisions used 0/3 · steps 5 |
| **Status** | **PASSING WITH FLAGS** |
| Source reliability | 0.9 — ACNC is the national charity regulator and this is its own Charity Register published under CC-BY, so identity, name and registration claims are authoritative. |
| Record id | composite ['ABN', 'Charity_Legal_Name'] — ABN alone is not safe: it has about 2% blanks and some rows (e.g. 859701-Y9K2G5 PAF) have none. Charity_Legal_Name is 200 distinct over 200 rows with no nulls. The composite of ABN and Charity_Legal_Name is therefore unique per register row even when ABN is blank. The source has no explicit record key column. |
| Observed at | dataset_modified → 2026-10-11 (basis: proxy) — No per-record extract or last-updated column exists. Registration_Date and Date_Organisation_Established are historical facts (valid_from material), not assertion times. The dataset is refreshed weekly, so the catalogue modified date is used as a weak proxy. |

## Mapping (10 field mappings from 69 source columns)

| canonical | ← source column | transforms | conf. | cond. | evidence |
|---|---|---|---|---|---|
| entity.abn | ABN | `["trim", "empty_to_null", "strip_float_suffix", "abn_normalize"]` | 0.95 |  | Column ABN holds 11-digit values such as 28679970527 and 80778454864. These are the charity's Australian Business Number, not an ACN, since all are 11 digits. About 2% are blank (e.g. the row named 859701-Y9K2G5 PAF). |
| entity.legal_name | Charity_Legal_Name | `["trim", "empty_to_null"]` | 0.95 |  | Charity_Legal_Name holds values like Caloola Union Church and ZAMZAM FOUNDATION INCORPORATED. These are the registered names of the charity, distinct from Other_Organisation_Names, which holds alternative names. |
| entity.trading_name | Other_Organisation_Names | `["trim", "empty_to_null", {"split": ","}]` | 0.75 |  | Other_Organisation_Names holds comma-packed alternative names such as 'ZamZam, ZamZam Foundation' and 'Allergy Life, Allergy Life Australia'. These are names other than the legal name, so they map to trading_name, one cl |
| address.full | Address_Line_1 | `["trim", "empty_to_null"]` | 0.7 |  | Address_Line_1 holds street lines such as '2837 Trunkey Rd' and '18 California Road'. It is the primary street line of the Business address and is only partial, since Address_Line_2 and Address_Line_3 are sparse continua |
| address.locality | Town_City | `["trim", "empty_to_null"]` | 0.92 |  | Town_City holds suburbs and towns such as Caloola, Oxley and Croydon South, which is the locality of the address. |
| address.state | State | `["trim", "empty_to_null", "state_normalize"]` | 0.95 |  | State holds Australian state abbreviations (NSW, QLD, VIC, SA, WA, NT, TAS, ACT) for the registered business address. It is not the Operates_in_* flags, which describe where the charity operates. |
| address.postcode | Postcode | `["trim", "empty_to_null", "strip_float_suffix", "postcode_normalize"]` | 0.93 |  | Postcode holds 4-digit values such as 2795, 4075 and 3134, which are the Australian postcodes of the business address. |
| address.country | Country | `["trim", "empty_to_null"]` | 0.92 |  | Country has the single value Australia for the business address. This is not Operating_Countries, which lists ISO codes for where the charity operates. |
| entity.website | Charity_Website | `["trim", "empty_to_null", "url_normalize"]` | 0.9 |  | Charity_Website holds URLs such as www.zamzam.org.au and https://www.warfrets.com.au. Some are Facebook pages, which are still the charity's declared web presence. Scheme-less values get http:// prepended. |
| entity.date_registered | Registration_Date | `["trim", "empty_to_null", {"parse_date": "%d/%m/%Y"}]` | 0.9 |  | Registration_Date holds values such as 03/12/2012 and 26/02/2013. The format is day-first, proved by 26/02/2013, 14/11/2021 and 27/11/2020, where the day exceeds 12. 03/12/2012 matches the 3 Dec 2012 start of ACNC regist |

## Validation — 350 held-out rows (loop set; final acceptance runs once after approval)

| check | threshold | result | pass |
|---|---|---|---|
| identifier checksum (entity.abn) | >= 95% | 100.0% (345 ok / 0 failed) | ✅ |
| enum legality (address.state) | >= 98% | 100.0% (306 ok / 0 failed) | ✅ |
| date parse (entity.date_registered) | >= 95% | 100.0% (349 ok / 0 failed) | ✅ |
| null drift (entity.abn ← ABN) | <= +2pp | -0.0% | ✅ |
| null drift (entity.legal_name ← Charity_Legal_Name) | <= +2pp | +0.0% | ✅ |
| null drift (entity.trading_name ← Other_Organisation_Names) | <= +2pp | +0.0% | ✅ |
| null drift (address.full ← Address_Line_1) | <= +2pp | -0.0% | ✅ |
| null drift (address.locality ← Town_City) | <= +2pp | +0.0% | ✅ |
| null drift (address.state ← State) | <= +2pp | -0.0% | ✅ |
| null drift (address.postcode ← Postcode) | <= +2pp | +0.0% | ✅ |
| null drift (address.country ← Country) | <= +2pp | +0.0% | ✅ |
| null drift (entity.website ← Charity_Website) | <= +2pp | +0.0% | ✅ |
| null drift (entity.date_registered ← Registration_Date) | <= +2pp | +0.0% | ✅ |
| record_id unique (full sample) | 0 duplicates | 0 duplicates | ✅ |
| minimum useful (a name or an identifier mapped) | required | yes | ✅ |

### Failing examples
none

## Semantic spot-check — 10 held-out records: 79 ok, 13 suspicious

| record | field | verdict | why |
|---|---|---|---|
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | entity.abn | ok | The ABN is in the charity's own ABN column and matches the charity named on the row. |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | entity.legal_name | ok | Charity_Legal_Name holds the registered company name, with the LTD suffix. |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | address.full | suspicious | Address_Line_1 is only the institution name 'Holy Trinity Lutheran College'; the actual street line '25 Trinity Drive' is in the unmapped Address_Line_2. |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | address.locality | ok | Horsham is a town and matches postcode 3400 and state VIC. |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | address.state | ok | VIC is consistent with Horsham 3400. |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | address.postcode | ok | 3400 is the Horsham postcode. |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | address.country | ok | Australia is the country of the business address. |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | entity.website | ok | The URL is the school's own website. |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | entity.date_registered | ok | Registration_Date equals Date_Organisation_Established (04/05/2021), so the value is the same under either reading. |
| 60684006102|IP INSIDERS LIMITED | entity.abn | ok | The ABN is in the charity's own ABN column on the row for IP INSIDERS LIMITED. |
| 60684006102|IP INSIDERS LIMITED | entity.legal_name | ok | Charity_Legal_Name holds the registered company name, with the LIMITED suffix. |
| 60684006102|IP INSIDERS LIMITED | address.full | ok | Address_Line_1 is the full street line, and Lines 2 and 3 are empty. |
| 60684006102|IP INSIDERS LIMITED | address.locality | ok | Hamilton (Brisbane) is consistent with postcode 4007 and QLD. |
| 60684006102|IP INSIDERS LIMITED | address.state | ok | QLD is consistent with postcode 4007; the VIC operating flag is a separate unmapped column. |
| 60684006102|IP INSIDERS LIMITED | address.postcode | ok | 4007 matches Hamilton QLD. |
| 60684006102|IP INSIDERS LIMITED | address.country | ok | Australia is the country of the business address. |
| 60684006102|IP INSIDERS LIMITED | entity.website | ok | The domain matches the organisation name, and http:// was added to a scheme-less value. |
| 60684006102|IP INSIDERS LIMITED | entity.date_registered | suspicious | Registration_Date (04/02/2025) is the ACNC charity registration date and differs from Date_Organisation_Established (28/01/2025), so it is not the entity's own  |
| 77105390237|National Capital Containers | entity.abn | ok | The ABN is in the charity's own ABN column on this row. |
| 77105390237|National Capital Containers | entity.legal_name | ok | It is copied from Charity_Legal_Name; the lack of a company suffix is plausible for an ACNC-listed entity. |
| 77105390237|National Capital Containers | address.full | ok | Address_Line_1 is a complete street line, and Lines 2 and 3 are empty. |
| 77105390237|National Capital Containers | address.locality | ok | Ngunnawal is an ACT suburb and matches postcode 2913. |
| 77105390237|National Capital Containers | address.state | ok | ACT matches Ngunnawal 2913; the NSW operating flag is a separate column. |
| 77105390237|National Capital Containers | address.postcode | ok | 2913 is the Ngunnawal postcode. |
| 77105390237|National Capital Containers | address.country | ok | Australia is the country of the business address. |
| 77105390237|National Capital Containers | entity.website | ok | It is the declared charity website, with http:// prepended to a scheme-less value. |
| 77105390237|National Capital Containers | entity.date_registered | ok | Registration_Date equals Date_Organisation_Established (06/08/2025), so the value is the same under either reading. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | entity.abn | ok | The ABN is in the charity's own ABN column on this row. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | entity.legal_name | ok | Charity_Legal_Name holds the registered name, with the Incorporated suffix. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | address.full | suspicious | 'PO BOX 105' is a postal address, not a street or premises address, yet the mapping presents it as the business address. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | address.locality | ok | Revesby North matches postcode 2212 and NSW. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | address.state | ok | NSW is consistent with postcode 2212. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | address.postcode | ok | 2212 is the Revesby postcode. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | address.country | ok | Australia is the country of the address. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | entity.website | ok | The URL is the charity's own website. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | entity.date_registered | suspicious | Registration_Date (28/04/2021) is the ACNC registration date and differs from Date_Organisation_Established (21/04/2021), so it is not the entity's own registra |
| 59646048320|YADAH SUS FOUNDATION LIMITED | entity.abn | ok | The ABN is in the charity's own ABN column on this row. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | entity.legal_name | ok | Charity_Legal_Name holds the registered company name, with the LIMITED suffix. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | entity.trading_name | suspicious | Other_Organisation_Names holds 'Geofrey Osawa', which is a person's name (likely a director or contact), not a trading or alternative organisation name. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | address.full | ok | Address_Line_1 is a complete street line, and Lines 2 and 3 are empty. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | address.locality | ok | Bennett Springs matches postcode 6063 and WA. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | address.state | ok | WA is consistent with postcode 6063. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | address.postcode | ok | 6063 is the Bennett Springs postcode. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | address.country | ok | Australia is the business address country; the Kenya operating country is a separate column. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | entity.website | ok | The domain matches the foundation's name, and http:// was added to a scheme-less value. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | entity.date_registered | suspicious | Registration_Date (19/12/2020) is the ACNC registration date and differs from Date_Organisation_Established (20/11/2020), so it is not the entity's own registra |
| 84337084591|Aboriginal children on Country Incorporated | entity.abn | ok | The ABN is in the charity's own ABN column on this row. |
| 84337084591|Aboriginal children on Country Incorporated | entity.legal_name | ok | Charity_Legal_Name holds the registered name, with the Incorporated suffix. |
| 84337084591|Aboriginal children on Country Incorporated | address.full | ok | 'U 2 210 Shellharbour Rd' is a complete street line, and Lines 2 and 3 are empty. |
| 84337084591|Aboriginal children on Country Incorporated | address.locality | ok | Port Kembla matches postcode 2505 and NSW. |
| 84337084591|Aboriginal children on Country Incorporated | address.state | ok | NSW is consistent with postcode 2505. |
| 84337084591|Aboriginal children on Country Incorporated | address.postcode | ok | 2505 is the Port Kembla postcode. |
| 84337084591|Aboriginal children on Country Incorporated | address.country | ok | Australia is the country of the address. |
| 84337084591|Aboriginal children on Country Incorporated | entity.website | ok | The URL is the charity's own website. |
| 84337084591|Aboriginal children on Country Incorporated | entity.date_registered | suspicious | Registration_Date (31/07/2025) is the ACNC registration date and differs from Date_Organisation_Established (30/07/2025), so it is not the entity's own registra |
| 21482069281|Hamilton Field Naturalists Club Inc. | entity.abn | ok | The ABN is in the charity's own ABN column on this row. |
| 21482069281|Hamilton Field Naturalists Club Inc. | entity.legal_name | ok | Charity_Legal_Name holds the registered name, with the Inc. suffix. |
| 21482069281|Hamilton Field Naturalists Club Inc. | entity.trading_name | ok | Other_Organisation_Names is the same name without 'Inc.', a reasonable alternative name. |
| 21482069281|Hamilton Field Naturalists Club Inc. | address.full | ok | Address_Line_1 is a complete street line, and Lines 2 and 3 are empty. |
| 21482069281|Hamilton Field Naturalists Club Inc. | address.locality | ok | Hamilton VIC matches postcode 3300. |
| 21482069281|Hamilton Field Naturalists Club Inc. | address.state | ok | VIC is consistent with postcode 3300. |
| 21482069281|Hamilton Field Naturalists Club Inc. | address.postcode | ok | 3300 is the Hamilton VIC postcode. |
| 21482069281|Hamilton Field Naturalists Club Inc. | address.country | ok | Australia is the country of the address. |
| 21482069281|Hamilton Field Naturalists Club Inc. | entity.website | ok | The URL is the club's own website. |
| 21482069281|Hamilton Field Naturalists Club Inc. | entity.date_registered | ok | Registration_Date equals Date_Organisation_Established (28/10/2024), so the value is the same under either reading. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | entity.abn | ok | The ABN is in the charity's own ABN column on this row. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | entity.legal_name | ok | Charity_Legal_Name holds the registered corporation name. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | address.full | ok | 'Melville Bay Road' is a street line with no number, which is a source limitation, and Lines 2 and 3 are empty. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | address.locality | ok | Nhulunbuy matches postcode 0880 and NT. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | address.state | ok | NT is consistent with postcode 0880. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | address.postcode | ok | 0880 keeps its leading zero and is the Nhulunbuy postcode. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | address.country | ok | Australia is the country of the address. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | entity.website | ok | The domain matches the organisation, with http:// added to a scheme-less value. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | entity.date_registered | suspicious | Registration_Date (21/09/2021) is the ACNC registration date; the organisation was established 21/04/2020, so the mapped value is not the entity's own registrat |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | entity.abn | ok | The ABN is in the charity's own ABN column on this row. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | entity.legal_name | suspicious | The name carries a trailing '. 8749', which looks like an ORIC/ICN registration number appended to the name rather than part of the registered name. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | address.full | ok | Address_Line_1 is a complete street line, and Lines 2 and 3 are empty. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | address.locality | ok | Tumbarumba matches postcode 2653 and NSW; it is in upper case in the source. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | address.state | ok | NSW is consistent with postcode 2653. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | address.postcode | ok | 2653 is the Tumbarumba postcode. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | address.country | ok | Australia is the country of the address. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | entity.website | ok | The URL is the organisation's own website. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | entity.date_registered | suspicious | Registration_Date (01/07/2021) is the ACNC registration date; the organisation was established 12/12/2017, so the mapped value is not the entity's own registrat |
| 85763061657|The Trustee for HOME BEYOND HOME | entity.abn | suspicious | The name is a trustee-style name, so the ABN may belong to the trustee or trust rather than the charity 'Home Beyond Home'; ownership is unclear. |
| 85763061657|The Trustee for HOME BEYOND HOME | entity.legal_name | suspicious | 'The Trustee for HOME BEYOND HOME' describes the trustee role, not the charity or trust itself; the party in legal_name may be the wrong one. |
| 85763061657|The Trustee for HOME BEYOND HOME | address.full | ok | 'U 14 1378 Lytton Rd' is a complete street line, and Lines 2 and 3 are empty. |
| 85763061657|The Trustee for HOME BEYOND HOME | address.locality | ok | Hemmant matches postcode 4174 and QLD. |
| 85763061657|The Trustee for HOME BEYOND HOME | address.state | ok | QLD is consistent with postcode 4174. |
| 85763061657|The Trustee for HOME BEYOND HOME | address.postcode | ok | 4174 is the Hemmant postcode. |
| 85763061657|The Trustee for HOME BEYOND HOME | address.country | ok | Australia is the country of the address. |
| 85763061657|The Trustee for HOME BEYOND HOME | entity.website | ok | The domain matches 'Home Beyond Home'. |
| 85763061657|The Trustee for HOME BEYOND HOME | entity.date_registered | suspicious | Registration_Date (20/12/2024) is the ACNC registration date and differs from Date_Organisation_Established (15/12/2024), so it is not the entity's own registra |

Notes: entity.date_registered is mapped from Registration_Date, which the evidence itself identifies as the ACNC charity registration date. In 7 of 10 records it differs from Date_Organisation_Established, so the config conflates charity registration with entity registration or incorporation. Either remap it or document the semantics.; address.full uses only Address_Line_1. In the Holy Trinity record the street number sits in the unmapped Address_Line_2, and PO Box values (Biyani House) are postal rather than premises addresses. Consider concatenating Lines 1-3 and flagging PO boxes.; Other_Organisation_Names is not reliably trading names. It held a person's name in one record (Yadah), so the mapping needs filtering or a lower confidence.; Charity_Legal_Name can hold trustee-style names ('The Trustee for ...') or names with a registry number appended ('. 8749'). Both break the 'as registered' meaning and may affect which party the ABN belongs to.

## Unmapped columns (59)

| source column | reason |
|---|---|
| Address_Type | Constant value Business; describes the address kind, no ontology field. |
| Address_Line_2 | Sparse continuation line (89% null) that sometimes holds a suburb; address.full uses Address_Line_1 only. |
| Address_Line_3 | Very sparse continuation line (98.5% null); no separate ontology field. |
| Date_Organisation_Established | Date the organisation was established, not registered with ACNC; contains placeholders such as 01/01/1900; no ontology field. |
| Charity_Size | Size classification (Small/Medium/Large), no ontology field. |
| Number_of_Responsible_Persons | Aggregate count, not an entity attribute in the ontology. |
| Financial_Year_End | Reporting period end, no ontology field. |
| Operates_in_ACT | Operating-jurisdiction flag, no ontology field; not the registered address state. |
| Operates_in_NSW | Operating-jurisdiction flag, no ontology field. |
| Operates_in_NT | Operating-jurisdiction flag, no ontology field. |
| Operates_in_QLD | Operating-jurisdiction flag, no ontology field. |
| Operates_in_SA | Operating-jurisdiction flag, no ontology field. |
| Operates_in_TAS | Operating-jurisdiction flag, no ontology field. |
| Operates_in_VIC | Operating-jurisdiction flag, no ontology field. |
| Operates_in_WA | Operating-jurisdiction flag, no ontology field. |
| Operating_Countries | List of ISO country codes where the charity operates, not the address country; no ontology field. |
| PBI | Public benevolent institution status flag, no ontology field. |
| HPC | Health promotion charity status flag, no ontology field. |
| Preventing_or_relieving_suffering_of_animals | Charitable purpose flag, no ontology field. |
| Advancing_Culture | Charitable purpose flag, no ontology field. |
| Advancing_Education | Charitable purpose flag, no ontology field. |
| Advancing_Health | Charitable purpose flag, no ontology field. |
| Promote_or_oppose_a_change_to_law__government_poll_or_prac | Charitable purpose flag, no ontology field. |
| Advancing_natual_environment | Charitable purpose flag, no ontology field. |
| Promoting_or_protecting_human_rights | Charitable purpose flag, no ontology field. |
| Purposes_beneficial_to_ther_general_public_and_other_analogous | Charitable purpose flag, no ontology field. |
| Promoting_reconciliation__mutual_respect_and_tolerance | Charitable purpose flag, no ontology field. |
| Advancing_Religion | Charitable purpose flag, no ontology field. |
| Advancing_social_or_public_welfare | Charitable purpose flag, no ontology field. |
| Advancing_security_or_safety_of_Australia_or_Australian_public | Charitable purpose flag, no ontology field. |
| Aboriginal_or_TSI | Beneficiary-group flag, no ontology field. |
| Adults | Beneficiary-group flag, no ontology field. |
| Aged_Persons | Beneficiary-group flag, no ontology field. |
| Children | Beneficiary-group flag, no ontology field. |
| Communities_Overseas | Beneficiary-group flag, no ontology field. |
| Early_Childhood | Beneficiary-group flag, no ontology field. |
| Ethnic_Groups | Beneficiary-group flag, no ontology field. |
| Families | Beneficiary-group flag, no ontology field. |
| Females | Beneficiary-group flag, no ontology field. |
| Financially_Disadvantaged | Beneficiary-group flag, no ontology field. |
| LGBTIQA+ | Beneficiary-group flag, no ontology field. |
| General_Community_in_Australia | Beneficiary-group flag, no ontology field. |
| Males | Beneficiary-group flag, no ontology field. |
| Migrants_Refugees_or_Asylum_Seekers | Beneficiary-group flag, no ontology field. |
| Other_Beneficiaries | Beneficiary-group flag, no ontology field. |
| Other_Charities | Beneficiary-group flag, no ontology field. |
| People_at_risk_of_homelessness | Beneficiary-group flag, no ontology field. |
| People_with_Chronic_Illness | Beneficiary-group flag, no ontology field. |
| People_with_Disabilities | Beneficiary-group flag, no ontology field. |
| Pre_Post_Release_Offenders | Beneficiary-group flag, no ontology field. |
| Rural_Regional_Remote_Communities | Beneficiary-group flag, no ontology field. |
| Unemployed_Person | Beneficiary-group flag, no ontology field. |
| Veterans_or_their_families | Beneficiary-group flag, no ontology field. |
| Victims_of_crime | Beneficiary-group flag, no ontology field. |
| Victims_of_Disasters | Beneficiary-group flag, no ontology field. |
| Youth | Beneficiary-group flag, no ontology field. |
| animals | Activity-tag flag, no ontology field. |
| environment | Activity-tag flag, no ontology field. |
| other_gender_identities | Beneficiary-group flag, no ontology field. |

## Side-by-side — 5 raw records vs their canonical observations

Read these for meaning, not parse success: is the date a registration date or a
licence date? Is the name the licensee or the applicant? Is the ABN the subject
entity's?

### Example 1 — source_record_id 46910265671|The Dunoon Family Foundation
RAW
```
ABN: 46910265671
Charity_Legal_Name: The Dunoon Family Foundation
Other_Organisation_Names: 
Address_Type: Business
Address_Line_1: 8 Spike Bar Way
Address_Line_2: 
Address_Line_3: 
Town_City: Moolap
State: VIC
Postcode: 3224
Country: Australia
Charity_Website: 
Registration_Date: 23/06/2021
Date_Organisation_Established: 23/06/2021
Charity_Size: Small
Number_of_Responsible_Persons: 4
Financial_Year_End: 30-Jun
Operates_in_ACT: 
Operates_in_NSW: 
Operates_in_NT: 
Operates_in_QLD: 
Operates_in_SA: 
Operates_in_TAS: 
Operates_in_VIC: Y
Operates_in_WA: 
Operating_Countries: AUS
PBI: 
HPC: 
Preventing_or_relieving_suffering_of_animals: 
Advancing_Culture: 
Advancing_Education: 
Advancing_Health: 
Promote_or_oppose_a_change_to_law__government_poll_or_prac: 
Advancing_natual_environment: 
Promoting_or_protecting_human_rights: 
Purposes_beneficial_to_ther_general_public_and_other_analogous: Y
Promoting_reconciliation__mutual_respect_and_tolerance: 
Advancing_Religion: 
Advancing_social_or_public_welfare: 
Advancing_security_or_safety_of_Australia_or_Australian_public: 
Aboriginal_or_TSI: 
Adults: 
Aged_Persons: 
Children: Y
Communities_Overseas: 
Early_Childhood: Y
Ethnic_Groups: 
Families: 
Females: 
Financially_Disadvantaged: 
LGBTIQA+: 
General_Community_in_Australia: 
Males: 
Migrants_Refugees_or_Asylum_Seekers: 
Other_Beneficiaries: 
Other_Charities: 
People_at_risk_of_homelessness: Y
People_with_Chronic_Illness: Y
People_with_Disabilities: 
Pre_Post_Release_Offenders: 
Rural_Regional_Remote_Communities: 
Unemployed_Person: 
Veterans_or_their_families: 
Victims_of_crime: 
Victims_of_Disasters: 
Youth: Y
animals: 
environment: 
other_gender_identities: 
```
CANONICAL
```
entity.abn = "46910265671"    (raw: "46910265671", field_confidence: 0.95)
entity.legal_name = "The Dunoon Family Foundation"    (raw: "The Dunoon Family Foundation", field_confidence: 0.95)
address.full = "8 Spike Bar Way"    (raw: "8 Spike Bar Way", field_confidence: 0.7)
address.locality = "Moolap"    (raw: "Moolap", field_confidence: 0.92)
address.state = "VIC"    (raw: "VIC", field_confidence: 0.95)
address.postcode = "3224"    (raw: "3224", field_confidence: 0.93)
address.country = "Australia"    (raw: "Australia", field_confidence: 0.92)
entity.date_registered = "2021-06-23"    (raw: "23/06/2021", field_confidence: 0.9)
```

### Example 2 — source_record_id 48638482514|MEDICAL AID AUSTRALIA LTD.
RAW
```
ABN: 48638482514
Charity_Legal_Name: MEDICAL AID AUSTRALIA LTD.
Other_Organisation_Names: 
Address_Type: Business
Address_Line_1: 6 Gunya ST  St
Address_Line_2: 
Address_Line_3: 
Town_City: Regents Park
State: NSW
Postcode: 2143
Country: Australia
Charity_Website: www.medaid.org.au
Registration_Date: 11/10/2021
Date_Organisation_Established: 26/02/2020
Charity_Size: Small
Number_of_Responsible_Persons: 4
Financial_Year_End: 30-Jun
Operates_in_ACT: 
Operates_in_NSW: 
Operates_in_NT: 
Operates_in_QLD: 
Operates_in_SA: 
Operates_in_TAS: 
Operates_in_VIC: 
Operates_in_WA: 
Operating_Countries: 
PBI: 
HPC: 
Preventing_or_relieving_suffering_of_animals: 
Advancing_Culture: 
Advancing_Education: 
Advancing_Health: Y
Promote_or_oppose_a_change_to_law__government_poll_or_prac: 
Advancing_natual_environment: 
Promoting_or_protecting_human_rights: 
Purposes_beneficial_to_ther_general_public_and_other_analogous: 
Promoting_reconciliation__mutual_respect_and_tolerance: 
Advancing_Religion: 
Advancing_social_or_public_welfare: 
Advancing_security_or_safety_of_Australia_or_Australian_public: 
Aboriginal_or_TSI: 
Adults: 
Aged_Persons: 
Children: 
Communities_Overseas: 
Early_Childhood: 
Ethnic_Groups: 
Families: 
Females: 
Financially_Disadvantaged: 
LGBTIQA+: 
General_Community_in_Australia: 
Males: 
Migrants_Refugees_or_Asylum_Seekers: 
Other_Beneficiaries: 
Other_Charities: 
People_at_risk_of_homelessness: 
People_with_Chronic_Illness: 
People_with_Disabilities: 
Pre_Post_Release_Offenders: 
Rural_Regional_Remote_Communities: 
Unemployed_Person: 
Veterans_or_their_families: 
Victims_of_crime: 
Victims_of_Disasters: 
Youth: 
animals: 
environment: 
other_gender_identities: 
```
CANONICAL
```
entity.abn = "48638482514"    (raw: "48638482514", field_confidence: 0.95)
entity.legal_name = "MEDICAL AID AUSTRALIA LTD."    (raw: "MEDICAL AID AUSTRALIA LTD.", field_confidence: 0.95)
address.full = "6 Gunya ST St"    (raw: "6 Gunya ST  St", field_confidence: 0.7)
address.locality = "Regents Park"    (raw: "Regents Park", field_confidence: 0.92)
address.state = "NSW"    (raw: "NSW", field_confidence: 0.95)
address.postcode = "2143"    (raw: "2143", field_confidence: 0.93)
address.country = "Australia"    (raw: "Australia", field_confidence: 0.92)
entity.website = "http://www.medaid.org.au"    (raw: "www.medaid.org.au", field_confidence: 0.9)
entity.date_registered = "2021-10-11"    (raw: "11/10/2021", field_confidence: 0.9)
```

### Example 3 — source_record_id 92635761527|THE AUSTRALASIAN SOCIETY FOR PHYSICAL ACTIVITY LTD
RAW
```
ABN: 92635761527
Charity_Legal_Name: THE AUSTRALASIAN SOCIETY FOR PHYSICAL ACTIVITY LTD
Other_Organisation_Names: 
Address_Type: Business
Address_Line_1: Deakin University Burwood
Address_Line_2: 
Address_Line_3: 
Town_City: Burwood
State: VIC
Postcode: 3125
Country: Australia
Charity_Website: www.aspactivity.org
Registration_Date: 22/10/2019
Date_Organisation_Established: 22/10/2019
Charity_Size: Small
Number_of_Responsible_Persons: 9
Financial_Year_End: 30-Jun
Operates_in_ACT: 
Operates_in_NSW: 
Operates_in_NT: 
Operates_in_QLD: 
Operates_in_SA: 
Operates_in_TAS: 
Operates_in_VIC: 
Operates_in_WA: 
Operating_Countries: AUS
PBI: 
HPC: Y
Preventing_or_relieving_suffering_of_animals: 
Advancing_Culture: 
Advancing_Education: Y
Advancing_Health: Y
Promote_or_oppose_a_change_to_law__government_poll_or_prac: 
Advancing_natual_environment: 
Promoting_or_protecting_human_rights: 
Purposes_beneficial_to_ther_general_public_and_other_analogous: 
Promoting_reconciliation__mutual_respect_and_tolerance: 
Advancing_Religion: 
Advancing_social_or_public_welfare: 
Advancing_security_or_safety_of_Australia_or_Australian_public: 
Aboriginal_or_TSI: Y
Adults: Y
Aged_Persons: Y
Children: Y
Communities_Overseas: Y
Early_Childhood: Y
Ethnic_Groups: Y
Families: Y
Females: Y
Financially_Disadvantaged: 
LGBTIQA+: 
General_Community_in_Australia: Y
Males: Y
Migrants_Refugees_or_Asylum_Seekers: 
Other_Beneficiaries: 
Other_Charities: 
People_at_risk_of_homelessness: 
People_with_Chronic_Illness: 
People_with_Disabilities: Y
Pre_Post_Release_Offenders: 
Rural_Regional_Remote_Communities: Y
Unemployed_Person: 
Veterans_or_their_families: 
Victims_of_crime: 
Victims_of_Disasters: 
Youth: Y
animals: 
environment: 
other_gender_identities: Y
```
CANONICAL
```
entity.abn = "92635761527"    (raw: "92635761527", field_confidence: 0.95)
entity.legal_name = "THE AUSTRALASIAN SOCIETY FOR PHYSICAL ACTIVITY LTD"    (raw: "THE AUSTRALASIAN SOCIETY FOR PHYSICAL AC", field_confidence: 0.95)
address.full = "Deakin University Burwood"    (raw: "Deakin University Burwood", field_confidence: 0.7)
address.locality = "Burwood"    (raw: "Burwood", field_confidence: 0.92)
address.state = "VIC"    (raw: "VIC", field_confidence: 0.95)
address.postcode = "3125"    (raw: "3125", field_confidence: 0.93)
address.country = "Australia"    (raw: "Australia", field_confidence: 0.92)
entity.website = "http://www.aspactivity.org"    (raw: "www.aspactivity.org", field_confidence: 0.9)
entity.date_registered = "2019-10-22"    (raw: "22/10/2019", field_confidence: 0.9)
```

### Example 4 — source_record_id 66230988037|VALOP Australia Charitable Trust
RAW
```
ABN: 66230988037
Charity_Legal_Name: VALOP Australia Charitable Trust
Other_Organisation_Names: 
Address_Type: Business
Address_Line_1: Se 211 430 Little Collins St
Address_Line_2: 
Address_Line_3: 
Town_City: Melbourne
State: VIC
Postcode: 3000
Country: Australia
Charity_Website: 
Registration_Date: 10/09/2020
Date_Organisation_Established: 26/06/2020
Charity_Size: Small
Number_of_Responsible_Persons: 2
Financial_Year_End: 30-Jun
Operates_in_ACT: 
Operates_in_NSW: 
Operates_in_NT: 
Operates_in_QLD: 
Operates_in_SA: 
Operates_in_TAS: 
Operates_in_VIC: 
Operates_in_WA: 
Operating_Countries: 
PBI: 
HPC: 
Preventing_or_relieving_suffering_of_animals: 
Advancing_Culture: 
Advancing_Education: Y
Advancing_Health: Y
Promote_or_oppose_a_change_to_law__government_poll_or_prac: 
Advancing_natual_environment: 
Promoting_or_protecting_human_rights: 
Purposes_beneficial_to_ther_general_public_and_other_analogous: 
Promoting_reconciliation__mutual_respect_and_tolerance: 
Advancing_Religion: Y
Advancing_social_or_public_welfare: 
Advancing_security_or_safety_of_Australia_or_Australian_public: 
Aboriginal_or_TSI: 
Adults: 
Aged_Persons: 
Children: 
Communities_Overseas: 
Early_Childhood: 
Ethnic_Groups: 
Families: 
Females: 
Financially_Disadvantaged: 
LGBTIQA+: 
General_Community_in_Australia: 
Males: 
Migrants_Refugees_or_Asylum_Seekers: 
Other_Beneficiaries: 
Other_Charities: 
People_at_risk_of_homelessness: 
People_with_Chronic_Illness: 
People_with_Disabilities: 
Pre_Post_Release_Offenders: 
Rural_Regional_Remote_Communities: 
Unemployed_Person: 
Veterans_or_their_families: 
Victims_of_crime: 
Victims_of_Disasters: 
Youth: 
animals: 
environment: 
other_gender_identities: 
```
CANONICAL
```
entity.abn = "66230988037"    (raw: "66230988037", field_confidence: 0.95)
entity.legal_name = "VALOP Australia Charitable Trust"    (raw: "VALOP Australia Charitable Trust", field_confidence: 0.95)
address.full = "Se 211 430 Little Collins St"    (raw: "Se 211 430 Little Collins St", field_confidence: 0.7)
address.locality = "Melbourne"    (raw: "Melbourne", field_confidence: 0.92)
address.state = "VIC"    (raw: "VIC", field_confidence: 0.95)
address.postcode = "3000"    (raw: "3000", field_confidence: 0.93)
address.country = "Australia"    (raw: "Australia", field_confidence: 0.92)
entity.date_registered = "2020-09-10"    (raw: "10/09/2020", field_confidence: 0.9)
```

### Example 5 — source_record_id 64670918279|SVETOCH LTD
RAW
```
ABN: 64670918279
Charity_Legal_Name: SVETOCH LTD
Other_Organisation_Names: 
Address_Type: Business
Address_Line_1: 17 Mexicali Court
Address_Line_2: 
Address_Line_3: 
Town_City: Broadbeach Waters
State: QLD
Postcode: 4218
Country: Australia
Charity_Website: https://svetoch.pro/
Registration_Date: 30/08/2023
Date_Organisation_Established: 30/08/2023
Charity_Size: Small
Number_of_Responsible_Persons: 4
Financial_Year_End: 30-Jun
Operates_in_ACT: 
Operates_in_NSW: 
Operates_in_NT: 
Operates_in_QLD: Y
Operates_in_SA: 
Operates_in_TAS: 
Operates_in_VIC: 
Operates_in_WA: 
Operating_Countries: AUS
PBI: 
HPC: 
Preventing_or_relieving_suffering_of_animals: 
Advancing_Culture: Y
Advancing_Education: 
Advancing_Health: 
Promote_or_oppose_a_change_to_law__government_poll_or_prac: 
Advancing_natual_environment: 
Promoting_or_protecting_human_rights: 
Purposes_beneficial_to_ther_general_public_and_other_analogous: 
Promoting_reconciliation__mutual_respect_and_tolerance: 
Advancing_Religion: 
Advancing_social_or_public_welfare: 
Advancing_security_or_safety_of_Australia_or_Australian_public: 
Aboriginal_or_TSI: 
Adults: Y
Aged_Persons: Y
Children: Y
Communities_Overseas: Y
Early_Childhood: Y
Ethnic_Groups: 
Families: 
Females: 
Financially_Disadvantaged: 
LGBTIQA+: 
General_Community_in_Australia: Y
Males: 
Migrants_Refugees_or_Asylum_Seekers: 
Other_Beneficiaries: 
Other_Charities: 
People_at_risk_of_homelessness: 
People_with_Chronic_Illness: 
People_with_Disabilities: 
Pre_Post_Release_Offenders: 
Rural_Regional_Remote_Communities: 
Unemployed_Person: 
Veterans_or_their_families: 
Victims_of_crime: 
Victims_of_Disasters: 
Youth: Y
animals: 
environment: 
other_gender_identities: 
```
CANONICAL
```
entity.abn = "64670918279"    (raw: "64670918279", field_confidence: 0.95)
entity.legal_name = "SVETOCH LTD"    (raw: "SVETOCH LTD", field_confidence: 0.95)
address.full = "17 Mexicali Court"    (raw: "17 Mexicali Court", field_confidence: 0.7)
address.locality = "Broadbeach Waters"    (raw: "Broadbeach Waters", field_confidence: 0.92)
address.state = "QLD"    (raw: "QLD", field_confidence: 0.95)
address.postcode = "4218"    (raw: "4218", field_confidence: 0.93)
address.country = "Australia"    (raw: "Australia", field_confidence: 0.92)
entity.website = "https://svetoch.pro/"    (raw: "https://svetoch.pro/", field_confidence: 0.9)
entity.date_registered = "2023-08-30"    (raw: "30/08/2023", field_confidence: 0.9)
```

## Your decision

Run exactly one of:

    firm onboard acnc-register --decide "approve"
    firm onboard acnc-register --decide "reject: <what is wrong and what to use instead>"
    firm onboard acnc-register --decide "abandon"

You never edit the config directly — a hand-edited config is hand-authored, and
the point is that it is not. Reject with a comment instead.