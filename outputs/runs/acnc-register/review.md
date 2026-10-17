# Mapping review — acnc-register

| | |
|---|---|
| Dataset | acnc-register — ACNC Registered Charities |
| Publisher / licence | Australian Charities and Not-for-profits Commission (ACNC) / cc-by |
| Resource | https://data.gov.au/data/dataset/b050b242-4487-4306-abf5-07ca073e5594/resource/8fb32972-24e9-4c95-885e-7140be51be8a/download/datadotgov_main.csv |
| Reader | {"format": "csv", "delimiter": ",", "encoding": "utf-8-sig", "header_row": 0, "sheet": null} |
| Agent run | revisions used 1/3 · steps 8 |
| **Status** | **PASSING WITH FLAGS** |
| Source reliability | 0.9 — ACNC is the national charity regulator and this is its own Charity Register published under CC-BY, so identity, name and registration claims are authoritative. |
| Record id | composite ['ABN', 'Charity_Legal_Name'] — ABN alone is not safe: it has about 2% blanks and some rows (e.g. 859701-Y9K2G5 PAF) have none. Charity_Legal_Name is 200 distinct over 200 rows with no nulls. The composite of ABN and Charity_Legal_Name is therefore unique per register row even when ABN is blank. The source has no explicit record key column. |
| Observed at | dataset_modified → 2026-10-11 (basis: proxy) — No per-record extract or last-updated column exists. Registration_Date and Date_Organisation_Established are historical facts (valid_from material), not assertion times. The dataset is refreshed weekly, so the catalogue modified date is used as a weak proxy. |

## Mapping (9 field mappings from 69 source columns)

| canonical | ← source column | transforms | conf. | cond. | evidence |
|---|---|---|---|---|---|
| entity.abn | ABN | `["trim", "empty_to_null", "strip_float_suffix", "abn_normalize"]` | 0.95 |  | Column ABN holds 11-digit values such as 28679970527 and 80778454864. These are the charity's Australian Business Number, not an ACN, since all are 11 digits. About 2% are blank (e.g. the row named 859701-Y9K2G5 PAF). |
| entity.legal_name | Charity_Legal_Name | `["trim", "empty_to_null"]` | 0.95 |  | Charity_Legal_Name holds values like Caloola Union Church and ZAMZAM FOUNDATION INCORPORATED. These are the registered names of the charity, distinct from Other_Organisation_Names, which holds alternative names. |
| entity.trading_name | Other_Organisation_Names | `["trim", "empty_to_null", {"split": ","}]` | 0.75 |  | Other_Organisation_Names holds comma-packed alternative names such as 'ZamZam, ZamZam Foundation' and 'Allergy Life, Allergy Life Australia'. These are names other than the legal name, so they map to trading_name, one cl |
| address.full | Address_Line_1 | `["trim", "empty_to_null"]` | 0.7 |  | Address_Line_1 holds street lines such as '2837 Trunkey Rd' and '18 California Road'. It is the primary street line of the Business address and is only partial, since Address_Line_2 and Address_Line_3 are sparse continua |
| address.locality | Town_City | `["trim", "empty_to_null"]` | 0.92 |  | Town_City holds suburbs and towns such as Caloola, Oxley and Croydon South, which is the locality of the address. |
| address.state | State | `["trim", "empty_to_null", "state_normalize"]` | 0.95 |  | State holds Australian state abbreviations (NSW, QLD, VIC, SA, WA, NT, TAS, ACT) for the registered business address. It is not the Operates_in_* flags, which describe where the charity operates. |
| address.postcode | Postcode | `["trim", "empty_to_null", "strip_float_suffix", "postcode_normalize"]` | 0.93 |  | Postcode holds 4-digit values such as 2795, 4075 and 3134, which are the Australian postcodes of the business address. |
| address.country | Country | `["trim", "empty_to_null", {"map_enum": {"mapping": {"Australia": "AU", "AU": "AU"}}}]` | 0.92 |  | Country has the single value Australia for the business address. Per the reviewer it is normalised to the ISO code 'AU' with map_enum. This is not Operating_Countries, which lists ISO codes for where the charity operates |
| entity.website | Charity_Website | `["trim", "empty_to_null", "url_normalize"]` | 0.9 |  | Charity_Website holds URLs such as www.zamzam.org.au and https://www.warfrets.com.au. Some are Facebook pages, which are still the charity's declared web presence. Scheme-less values get http:// prepended. |

## Validation — 350 held-out rows (loop set; final acceptance runs once after approval)

| check | threshold | result | pass |
|---|---|---|---|
| identifier checksum (entity.abn) | >= 95% | 100.0% (345 ok / 0 failed) | ✅ |
| enum legality (address.state) | >= 98% | 100.0% (306 ok / 0 failed) | ✅ |
| null drift (entity.abn ← ABN) | <= +2pp | -0.0% | ✅ |
| null drift (entity.legal_name ← Charity_Legal_Name) | <= +2pp | +0.0% | ✅ |
| null drift (entity.trading_name ← Other_Organisation_Names) | <= +2pp | +0.0% | ✅ |
| null drift (address.full ← Address_Line_1) | <= +2pp | -0.0% | ✅ |
| null drift (address.locality ← Town_City) | <= +2pp | +0.0% | ✅ |
| null drift (address.state ← State) | <= +2pp | -0.0% | ✅ |
| null drift (address.postcode ← Postcode) | <= +2pp | +0.0% | ✅ |
| null drift (address.country ← Country) | <= +2pp | +0.0% | ✅ |
| null drift (entity.website ← Charity_Website) | <= +2pp | +0.0% | ✅ |
| record_id effectively unique (full sample) | <= 0.5% duplicates | 0 duplicates (0.00%) | ✅ |
| minimum useful (a name or an identifier mapped) | required | yes | ✅ |

### Failing examples
none

## Semantic spot-check — 10 held-out records: 77 ok, 5 suspicious

| record | field | verdict | why |
|---|---|---|---|
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | entity.abn | ok | The 11-digit ABN passes the checksum and sits on the same row as the college's legal name. |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | entity.legal_name | ok | Charity_Legal_Name is the registered company name, with the LTD suffix. |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | address.full | suspicious | Address_Line_1 holds only the institution name 'Holy Trinity Lutheran College', and the actual street line '25 Trinity Drive' is in the unmapped Address_Line_2, |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | address.locality | ok | Horsham is a town and matches postcode 3400 in VIC. |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | address.state | ok | VIC is the business address state and is consistent with the postcode. |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | address.postcode | ok | 3400 is the Horsham postcode. |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | address.country | ok | Australia maps to AU. |
| 90649930049|HOLY TRINITY LUTHERAN COLLEGE LTD | entity.website | ok | The URL is the school's own domain. |
| 60684006102|IP INSIDERS LIMITED | entity.abn | ok | The 11-digit ABN is on the row of the named charity. |
| 60684006102|IP INSIDERS LIMITED | entity.legal_name | ok | IP INSIDERS LIMITED is the registered company name. |
| 60684006102|IP INSIDERS LIMITED | address.full | ok | Address_Line_1 is a unit and street line and Address_Line_2 is empty. The 'Tnhs' prefix is odd but is source text. |
| 60684006102|IP INSIDERS LIMITED | address.locality | ok | Hamilton, QLD matches postcode 4007. |
| 60684006102|IP INSIDERS LIMITED | address.state | ok | QLD is consistent with the Hamilton postcode. The Operates_in_VIC flag is a separate field and was not used. |
| 60684006102|IP INSIDERS LIMITED | address.postcode | ok | 4007 is a Hamilton QLD postcode. |
| 60684006102|IP INSIDERS LIMITED | address.country | ok | Australia maps to AU. Operating_Countries was not used. |
| 60684006102|IP INSIDERS LIMITED | entity.website | ok | The scheme-less URL had http:// prepended and the domain matches the charity name. |
| 77105390237|National Capital Containers | entity.abn | ok | The ABN is on the row's own subject entity and no agent or parent ABN column exists. |
| 77105390237|National Capital Containers | entity.legal_name | ok | It is a verbatim copy of Charity_Legal_Name. The name has no company suffix and reads like a trading name, but no other name column exists to compare it with. |
| 77105390237|National Capital Containers | address.full | ok | '15 Margany Cl' is a complete street line and the continuation lines are empty. |
| 77105390237|National Capital Containers | address.locality | ok | Ngunnawal is an ACT suburb and matches postcode 2913. |
| 77105390237|National Capital Containers | address.state | ok | ACT is consistent with the Ngunnawal suburb and postcode. |
| 77105390237|National Capital Containers | address.postcode | ok | 2913 is the Ngunnawal postcode. |
| 77105390237|National Capital Containers | address.country | ok | Australia maps to AU. |
| 77105390237|National Capital Containers | entity.website | ok | The URL is the entity's declared site, with http:// prepended. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | entity.abn | ok | The ABN is on the row of the named incorporated association. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | entity.legal_name | ok | It is the registered name, including 'Incorporated'. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | address.full | suspicious | 'PO BOX 105' is a postal address, not a premises or registered street address, so it should not be stored as a general full address without a postal/street dist |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | address.locality | ok | Revesby North is a locality and matches postcode 2212. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | address.state | ok | NSW is consistent with the postcode. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | address.postcode | ok | 2212 is the Revesby postcode and goes with the PO Box. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | address.country | ok | Australia maps to AU. |
| 65351615350|Biyani House Revesby Women's Shelter Incorporated | entity.website | ok | The URL is the shelter's own site. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | entity.abn | ok | The ABN is on the row of the named foundation. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | entity.legal_name | ok | YADAH SUS FOUNDATION LIMITED is the registered company name. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | entity.trading_name | suspicious | 'Geofrey Osawa' is a person's name (probably a responsible person or contact), not a trading name of the foundation. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | address.full | ok | '37 constellations drive' is a plain street line. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | address.locality | ok | Bennett Springs is a WA suburb and matches postcode 6063. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | address.state | ok | WA is consistent with the postcode. The Operates_in_WA flag is blank but unrelated to the address. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | address.postcode | ok | 6063 matches Bennett Springs. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | address.country | ok | Australia is the address country. Operating_Countries is KEN, a separate field that was not used. |
| 59646048320|YADAH SUS FOUNDATION LIMITED | entity.website | ok | The scheme-less domain had http:// prepended, and the trailing slash is harmless. |
| 84337084591|Aboriginal children on Country Incorporated | entity.abn | ok | The ABN is on the row of the named association. |
| 84337084591|Aboriginal children on Country Incorporated | entity.legal_name | ok | It is the registered name, including 'Incorporated'. |
| 84337084591|Aboriginal children on Country Incorporated | address.full | ok | 'U 2 210 Shellharbour Rd' is a unit and street line. |
| 84337084591|Aboriginal children on Country Incorporated | address.locality | ok | Port Kembla matches postcode 2505 in NSW. |
| 84337084591|Aboriginal children on Country Incorporated | address.state | ok | NSW is consistent with the postcode. |
| 84337084591|Aboriginal children on Country Incorporated | address.postcode | ok | 2505 is the Port Kembla postcode. |
| 84337084591|Aboriginal children on Country Incorporated | address.country | ok | Australia maps to AU. |
| 84337084591|Aboriginal children on Country Incorporated | entity.website | ok | The URL is the organisation's own domain. |
| 21482069281|Hamilton Field Naturalists Club Inc. | entity.abn | ok | The ABN is on the row of the named club. |
| 21482069281|Hamilton Field Naturalists Club Inc. | entity.legal_name | ok | 'Inc.' marks the registered incorporated name. |
| 21482069281|Hamilton Field Naturalists Club Inc. | entity.trading_name | ok | It is the same name without 'Inc.', a genuine alternative name and not a person or other party. |
| 21482069281|Hamilton Field Naturalists Club Inc. | address.full | ok | '333 North Boundary Rd' is a street line. |
| 21482069281|Hamilton Field Naturalists Club Inc. | address.locality | ok | Hamilton, VIC matches postcode 3300. |
| 21482069281|Hamilton Field Naturalists Club Inc. | address.state | ok | VIC is consistent with the postcode. |
| 21482069281|Hamilton Field Naturalists Club Inc. | address.postcode | ok | 3300 is the Hamilton VIC postcode. |
| 21482069281|Hamilton Field Naturalists Club Inc. | address.country | ok | Australia maps to AU. |
| 21482069281|Hamilton Field Naturalists Club Inc. | entity.website | ok | The URL is the club's own domain. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | entity.abn | ok | The ABN is on the row of the named corporation. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | entity.legal_name | ok | It is the registered corporation name. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | address.full | ok | 'Melville Bay Road' has no street number but is a genuine street line. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | address.locality | ok | Nhulunbuy is an NT town and matches postcode 0880. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | address.state | ok | NT is consistent with the postcode. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | address.postcode | ok | 0880 keeps its leading zero and is correct for Nhulunbuy. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | address.country | ok | Australia maps to AU. |
| 37690427467|North East Arnhem Land Aboriginal Corporation | entity.website | ok | The URL is the entity's own domain, with http:// prepended. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | entity.abn | ok | The ABN is on the row of the named corporation. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | entity.legal_name | suspicious | The value carries a trailing '. 8749', which looks like an ICN registration number appended to the name. It is a verbatim copy, but it may not be the name exact |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | address.full | ok | '15 Lyne Street East' is a street line. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | address.locality | ok | TUMBARUMBA is an NSW town and matches postcode 2653. It is upper-case but correct. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | address.state | ok | NSW is consistent with the postcode. The Operates_in_ACT flag was not used. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | address.postcode | ok | 2653 is the Tumbarumba postcode. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | address.country | ok | Australia maps to AU. |
| 90686129629|Ngarigo Nation Indigenous Corporation. 8749 | entity.website | ok | The URL is the entity's own domain. |
| 85763061657|The Trustee for HOME BEYOND HOME | entity.abn | ok | The ABN is on the row's own entity. It is presumably the trust's ABN, which goes with the trustee-style name. |
| 85763061657|The Trustee for HOME BEYOND HOME | entity.legal_name | suspicious | 'The Trustee for HOME BEYOND HOME' names the trustee capacity of a trust, not the charity's own name 'Home Beyond Home'. The name or entity type should be revie |
| 85763061657|The Trustee for HOME BEYOND HOME | address.full | ok | 'U 14 1378 Lytton Rd' is a unit and street line. |
| 85763061657|The Trustee for HOME BEYOND HOME | address.locality | ok | Hemmant is a QLD suburb and matches postcode 4174. |
| 85763061657|The Trustee for HOME BEYOND HOME | address.state | ok | QLD is consistent with the postcode. |
| 85763061657|The Trustee for HOME BEYOND HOME | address.postcode | ok | 4174 is the Hemmant postcode. |
| 85763061657|The Trustee for HOME BEYOND HOME | address.country | ok | Australia maps to AU. |
| 85763061657|The Trustee for HOME BEYOND HOME | entity.website | ok | The URL is the charity's own domain. |

Notes: Address_Line_1 alone as address.full is unreliable: Address_Line_2 and Address_Line_3 are dropped, and record 90649930049 shows the street line sitting in Address_Line_2 behind a building-name line in Line_1. The config should concatenate Lines 1-3.; Other_Organisation_Names is not reliably a trading-name field: it can hold person names (Geofrey Osawa), so splitting it into trading_name risks wrong-party claims.; Charity_Legal_Name sometimes contains trustee wording ('The Trustee for ...') or a registration-number suffix ('. 8749'), so it may not equal the registered name of the entity.; PO Box values appear in the Business address column, so premises and postal addresses are mixed.; Registration_Date and Date_Organisation_Established are correctly left unmapped, since neither is a company registration date. The ABN column was only length-checked here (one ABN was checksum-verified by hand), so checksum validation should stay in the pipeline.

## Unmapped columns (60)

| source column | reason |
|---|---|
| Address_Type | Constant value Business; describes the address kind, no ontology field. |
| Address_Line_2 | Sparse continuation line (89% null) that sometimes holds a suburb; address.full uses Address_Line_1 only. |
| Address_Line_3 | Very sparse continuation line (98.5% null); no separate ontology field. |
| Registration_Date | Date ACNC granted charity status, not the entity's own registration date. The separate Date_Organisation_Established column shows the source distinguishes the two, and pre-2012 organisations are all clamped to ACNC's Dec-2012 launch, a systematic bias that mapping cannot fix. Unmapped on reviewer instruction. |
| Date_Organisation_Established | 'Established' is not 'registered', so it is not remapped to date_registered. It also holds 01/01/1900 placeholders. Unmapped on reviewer instruction; no ontology field. |
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
address.country = "AU"    (raw: "Australia", field_confidence: 0.92)
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
address.country = "AU"    (raw: "Australia", field_confidence: 0.92)
entity.website = "http://www.medaid.org.au"    (raw: "www.medaid.org.au", field_confidence: 0.9)
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
address.country = "AU"    (raw: "Australia", field_confidence: 0.92)
entity.website = "http://www.aspactivity.org"    (raw: "www.aspactivity.org", field_confidence: 0.9)
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
address.country = "AU"    (raw: "Australia", field_confidence: 0.92)
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
address.country = "AU"    (raw: "Australia", field_confidence: 0.92)
entity.website = "https://svetoch.pro/"    (raw: "https://svetoch.pro/", field_confidence: 0.9)
```

## Your decision

Run exactly one of:

    firm onboard acnc-register --decide "approve"
    firm onboard acnc-register --decide "reject: <what is wrong and what to use instead>"
    firm onboard acnc-register --decide "abandon"

You never edit the config directly — a hand-edited config is hand-authored, and
the point is that it is not. Reject with a comment instead.