# Mapping review — business-discount-directory

| | |
|---|---|
| Dataset | business-discount-directory — Business Discount Directory |
| Publisher / licence | Customer Services, Open Data and Small and Family Business / CC-BY-4.0 |
| Resource | https://www.data.qld.gov.au/dataset/fac8c9a4-03d5-44c6-9a9e-bb81085b0a44/resource/33159533-c2ee-4e11-902d-e2d250e2c84c/download/opendata-discount-offers-20260917170016.csv |
| Reader | {"format": "csv", "delimiter": ",", "encoding": "utf-8-sig", "header_row": 0, "sheet": null} |
| Agent run | revisions used 0/3 · steps 5 |
| **Status** | **PASSING WITH FLAGS** |
| Source reliability | 0.6 — A state government directory of businesses that self-register for the discount schemes: official and curated, but the contact and business details are supplied by the businesses themselves and not verified against a register, and it carries no ABN or ACN. |
| Record id | row_hash [] — The source has no record key, and no ABN or ACN either. Trading Name has 84 distinct values and Outlet Name 109 across 200 rows, so neither is unique. Telephone Number has 172 distinct values, and Outlet Address has 161 distinct values with 11% nulls, so neither is unique either. No plausible composite is shown to be unique over the full sample, so row_hash is the safe choice. |
| Observed at | dataset_modified → 2026-09-24 (basis: proxy) — The file has no per-record extract or last-updated date column. The only dated information is the catalogue modified date, so dataset_modified is used as a weak proxy. |

## Mapping (5 field mappings from 18 source columns)

| canonical | ← source column | transforms | conf. | cond. | evidence |
|---|---|---|---|---|---|
| entity.trading_name | Trading Name | `["trim", "empty_to_null"]` | 0.9 |  | Column 'Trading Name' holds values like 'Amplifon', 'Andersens Floor Coverings' and 'Access Dental Services Pty Ltd'. These are the names the businesses trade under in the discount directory, repeated across their outlet |
| entity.website | Website | `["trim", "empty_to_null", "url_normalize"]` | 0.8 |  | Column 'Website' holds values like 'http://www.andersens.com.au', 'http://adpa.com.au' and 'https://andrewsairportpark.com.au'. They are the business's web address. Some are malformed at source, e.g. 'http://https://www. |
| address.full | Outlet Address | `["trim", "empty_to_null"]` | 0.7 |  | Column 'Outlet Address' holds values like '10 Herberton St', '179 Nicklin Way' and 'Shop 124, Mount Pleasant Shopping Centre'. It is the street-level address of the outlet, so it is the physical address and not a postal  |
| address.locality | Outlet Suburb | `["trim", "empty_to_null"]` | 0.92 |  | Column 'Outlet Suburb' holds values like 'MACKAY', 'TWEED HEADS SOUTH' and 'MAROOCHYDORE'. These are suburb or town names of the outlet, so address.locality. The rest of the address is in separate columns. |
| address.postcode | Outlet Postcode | `["trim", "empty_to_null", "postcode_normalize"]` | 0.93 |  | Column 'Outlet Postcode' holds values like '4740', '2486' and '3216'. They are all 4-digit Australian postcodes of the outlet. postcode_normalize zero-pads any that lost a leading zero. |

## Validation — 350 held-out rows (loop set; final acceptance runs once after approval)

| check | threshold | result | pass |
|---|---|---|---|
| null drift (entity.trading_name ← Trading Name) | <= +2pp | +0.0% | ✅ |
| null drift (entity.website ← Website) | <= +2pp | -0.0% | ✅ |
| null drift (address.full ← Outlet Address) | <= +2pp | +0.0% | ✅ |
| null drift (address.locality ← Outlet Suburb) | <= +2pp | +0.0% | ✅ |
| null drift (address.postcode ← Outlet Postcode) | <= +2pp | +0.0% | ✅ |
| record_id effectively unique (full sample) | <= 0.5% duplicates | 1 duplicates (0.29%) | ✅ |
| minimum useful (a name or an identifier mapped) | required | yes | ✅ |

### Failing examples
none

## Semantic spot-check — 10 held-out records: 41 ok, 7 suspicious

| record | field | verdict | why |
|---|---|---|---|
| a8ad7ecfb0ece669 | entity.trading_name | ok | 'Amplifon' is the brand name from the Trading Name column and is not a registered legal name. |
| a8ad7ecfb0ece669 | entity.website | suspicious | The source URL is malformed ('http://https://...') and the canonical value ends '...AUORG1PKAVT6A00', which does not match the raw cell, so the value was altere |
| a8ad7ecfb0ece669 | address.full | ok | 'U 4, 107-111 Queen St' is a genuine street line for the Cleveland outlet, but it has no suburb, state or postcode, so it is a partial address. |
| a8ad7ecfb0ece669 | address.locality | ok | 'CLEVELAND' is the outlet suburb and fits postcode 4163. |
| a8ad7ecfb0ece669 | address.postcode | ok | 4163 is a valid Cleveland QLD postcode and matches the Outlet Postcode column. |
| 3373db45d8d72436 | entity.trading_name | ok | 'Angus & Coote' is the brand name and matches the Outlet Name. |
| 3373db45d8d72436 | entity.website | ok | It is a clean brand website URL copied from the Website column. |
| 3373db45d8d72436 | address.full | suspicious | 'Castletown Shp Cnt' is a shopping centre name, not a street address, and it is mapped to address.full. |
| 3373db45d8d72436 | address.locality | ok | 'HYDE PARK' is the outlet suburb (Townsville) and is consistent with postcode 4812. |
| 3373db45d8d72436 | address.postcode | ok | 4812 matches Hyde Park QLD. |
| 414de081d51ecd99 | entity.trading_name | ok | It is the brand name from the Trading Name column. |
| 414de081d51ecd99 | entity.website | ok | It is a valid brand website URL. |
| 414de081d51ecd99 | address.full | suspicious | 'Central Highlands Market Place' is a centre or venue name, not a street address. |
| 414de081d51ecd99 | address.locality | ok | 'EMERALD' is the outlet suburb and fits postcode 4720. |
| 414de081d51ecd99 | address.postcode | ok | 4720 matches Emerald QLD. |
| f8f6df06cafb6d3b | entity.trading_name | ok | It is a trading name for the brand, though the outlet-level name is 'Andersens Carpets', so the brand-level value was chosen over the outlet-specific one. |
| f8f6df06cafb6d3b | entity.website | ok | It is a valid brand website URL. |
| f8f6df06cafb6d3b | address.full | ok | '36 Duke St' is a real street address for the Gympie outlet. |
| f8f6df06cafb6d3b | address.locality | ok | 'GYMPIE' is the outlet suburb. |
| f8f6df06cafb6d3b | address.postcode | ok | 4570 matches Gympie. |
| 9bf76a92aa7e1a75 | entity.trading_name | ok | 'Aksa Home Decor' is the trading name and also matches the Outlet Name. |
| 9bf76a92aa7e1a75 | entity.website | ok | It is a valid website URL for an online-capable business. |
| 9bf76a92aa7e1a75 | address.locality | ok | 'KILLARA' is the outlet suburb. |
| 9bf76a92aa7e1a75 | address.postcode | ok | 2071 matches Killara NSW. |
| f9aad4867a42037c | entity.trading_name | ok | It is the brand-level trading name, while the outlet name is 'Andersens Carpets'. |
| f9aad4867a42037c | entity.website | ok | It is a valid brand website URL. |
| f9aad4867a42037c | address.full | ok | 'Shop 4 1 Greenway Dr' is a street address, with a double space collapsed. |
| f9aad4867a42037c | address.locality | ok | 'TWEED HEADS' is the outlet suburb. |
| f9aad4867a42037c | address.postcode | ok | 2485 matches Tweed Heads. |
| ab772061675d9a9d | entity.trading_name | ok | 'Arthurs Autoglass' is the brand trading name, while the outlet trades as 'Morayfield Discount Autoglass', so it is acceptable but not outlet-specific. |
| ab772061675d9a9d | entity.website | ok | It is an outlet-specific website URL and is a valid web address. |
| ab772061675d9a9d | address.full | ok | '125 Morayfield Rd' is a street address. |
| ab772061675d9a9d | address.locality | ok | 'CABOOLTURE SOUTH' is the outlet suburb. |
| ab772061675d9a9d | address.postcode | ok | 4510 is consistent with Caboolture South. |
| 8797e54e37a80189 | entity.trading_name | suspicious | 'ADPA Ltd' carries a company suffix and looks like a legal or organisation name, while the outlet name is 'ADPAQ', so the party type is uncertain. |
| 8797e54e37a80189 | entity.website | ok | It is a valid website URL. |
| 8797e54e37a80189 | address.full | ok | 'Shop 109 137 Laver Dr' is a street address. |
| 8797e54e37a80189 | address.locality | ok | 'ROBINA' is the outlet suburb. |
| 8797e54e37a80189 | address.postcode | ok | 4226 matches Robina QLD. |
| 86f9d51258089cb6 | entity.trading_name | suspicious | 'Ali Baba Lebanese Cuisine Pty Ltd' includes 'Pty Ltd', so it is a registered company name placed in trading_name; it probably belongs in legal_name. |
| 86f9d51258089cb6 | address.full | suspicious | 'Sunshine Plaza' is a shopping centre name, not a street address. |
| 86f9d51258089cb6 | address.locality | ok | 'MAROOCHYDORE' is the outlet suburb. |
| 86f9d51258089cb6 | address.postcode | ok | 4558 matches Maroochydore. |
| 7655e30afe549885 | entity.trading_name | ok | It is the brand trading name and matches the Outlet Name. |
| 7655e30afe549885 | entity.website | ok | It is a valid brand website URL. |
| 7655e30afe549885 | address.full | suspicious | 'Caneland Central Shp Cnt' is a shopping centre name, not a street address. |
| 7655e30afe549885 | address.locality | ok | 'MACKAY' is the outlet suburb. |
| 7655e30afe549885 | address.postcode | ok | 4740 matches Mackay. |

Notes: Outlet Address is often a shopping centre or venue name ('Castletown Shp Cnt', 'Sunshine Plaza', 'Caneland Central Shp Cnt', 'Central Highlands Market Place'), not a street address. Mapping it to address.full without a conditional is questionable, and address.full holds only the street line, not a full address.; Trading Name sometimes holds a registered-style name ('Ali Baba Lebanese Cuisine Pty Ltd', 'ADPA Ltd'), so legal names can leak into trading_name. Outlet Name is a distinct, outlet-level trading name that is left unmapped.; The website value for the Amplifon record differs from the raw cell (extra '6A00' suffix) and keeps the malformed 'http://https://' prefix. url_normalize is not repairing or faithfully preserving the value.; No address.state is mapped even though the dataset is Queensland and NSW only, so every address lacks a state.

## Unmapped columns (13)

| source column | reason |
|---|---|
| Outlet Name | Outlet-level label such as 'Amplifon Mackay', 'ADPAQ' or 'Allcracft Sewing Machines' (a typo of the trading name). It is neither the registered legal name nor clearly a trading name, so it is not mapped. |
| Telephone Number | No telephone field in the ontology. |
| Online Mail Order Flag | Scheme attribute (Yes/No) with no ontology field. |
| Australia Wide Flag | Scheme attribute (Yes/No) describing offer coverage, with no ontology field. |
| Overseas Flag | Scheme attribute (Yes/No) with no ontology field. |
| Senior Scheme Flag | Scheme-participation flag with no ontology field. It is 'Yes' on every profiled row. |
| Carer Scheme Flag | Scheme-participation flag with no ontology field. |
| Business Category | Directory-specific category such as 'Dentists' or 'Pharmacies', not an ANZSIC code, so it should not go in entity.industry_code. |
| Discount | Free-text description of the discount offer, with no ontology field. It is also truncated at about 60 characters in the profile. |
| Latitude | Geocoordinate with no ontology field. It holds 0 as a placeholder for unknown on some rows. |
| Longitude | Geocoordinate with no ontology field. It holds 0 as a placeholder for unknown on some rows. |
| Mobile Business Flag | Scheme attribute (Yes/No) with no ontology field. |
| Parent Business Category | Directory-specific top-level category such as 'Health and Medical', not an ANZSIC code or other ontology field. |

## Side-by-side — 5 raw records vs their canonical observations

Read these for meaning, not parse success: is the date a registration date or a
licence date? Is the name the licensee or the applicant? Is the ABN the subject
entity's?

### Example 1 — source_record_id 9080de1440969eca
RAW
```
Trading Name: Andersens Floor Coverings
Outlet Name: Andersens Carpets
Website: http://www.andersens.com.au
Outlet Address: 36 Brisbane Rd
Outlet Suburb: BUNDAMBA
Outlet Postcode: 4305
Telephone Number: (07) 3282 7000
Online Mail Order Flag: No
Australia Wide Flag: Yes
Overseas Flag: Yes
Senior Scheme Flag: Yes
Carer Scheme Flag: Yes
Business Category: Tile Products and Services
Discount: 15% off ticketed price. Not valid with any other offer.
Latitude: -27.60793
Longitude: 152.81166
Mobile Business Flag: No
Parent Business Category: Trade Services
```
CANONICAL
```
entity.trading_name = "Andersens Floor Coverings"    (raw: "Andersens Floor Coverings", field_confidence: 0.9)
entity.website = "http://www.andersens.com.au"    (raw: "http://www.andersens.com.au", field_confidence: 0.8)
address.full = "36 Brisbane Rd"    (raw: "36 Brisbane Rd", field_confidence: 0.7)
address.locality = "BUNDAMBA"    (raw: "BUNDAMBA", field_confidence: 0.92)
address.postcode = "4305"    (raw: "4305", field_confidence: 0.93)
```

### Example 2 — source_record_id b827ba0529931ac0
RAW
```
Trading Name: Andersens Floor Coverings
Outlet Name: Andersens Carpets
Website: http://www.andersens.com.au
Outlet Address: 17 Mabel St
Outlet Suburb: ATHERTON
Outlet Postcode: 4883
Telephone Number: (07) 4091 3300
Online Mail Order Flag: No
Australia Wide Flag: Yes
Overseas Flag: Yes
Senior Scheme Flag: Yes
Carer Scheme Flag: Yes
Business Category: Blinds and Awnings
Discount: 15% off ticketed price. Not valid with any other offer.
Latitude: -17.26435
Longitude: 145.47777
Mobile Business Flag: No
Parent Business Category: House and Home
```
CANONICAL
```
entity.trading_name = "Andersens Floor Coverings"    (raw: "Andersens Floor Coverings", field_confidence: 0.9)
entity.website = "http://www.andersens.com.au"    (raw: "http://www.andersens.com.au", field_confidence: 0.8)
address.full = "17 Mabel St"    (raw: "17 Mabel St", field_confidence: 0.7)
address.locality = "ATHERTON"    (raw: "ATHERTON", field_confidence: 0.92)
address.postcode = "4883"    (raw: "4883", field_confidence: 0.93)
```

### Example 3 — source_record_id c6645fe59dc7c286
RAW
```
Trading Name: ADPA Ltd
Outlet Name: ADPAQ
Website: http://adpa.com.au
Outlet Address: U 9  521 Beams Rd
Outlet Suburb: CARSELDINE
Outlet Postcode: 4034
Telephone Number: (07) 3263 8632
Online Mail Order Flag: No
Australia Wide Flag: Yes
Overseas Flag: No
Senior Scheme Flag: Yes
Carer Scheme Flag: Yes
Business Category: Dental Prosthetists
Discount: Complimentary consultation for denture assessment.
Latitude: -27.34823
Longitude: 153.02756
Mobile Business Flag: No
Parent Business Category: Health and Medical
```
CANONICAL
```
entity.trading_name = "ADPA Ltd"    (raw: "ADPA Ltd", field_confidence: 0.9)
entity.website = "http://adpa.com.au"    (raw: "http://adpa.com.au", field_confidence: 0.8)
address.full = "U 9 521 Beams Rd"    (raw: "U 9  521 Beams Rd", field_confidence: 0.7)
address.locality = "CARSELDINE"    (raw: "CARSELDINE", field_confidence: 0.92)
address.postcode = "4034"    (raw: "4034", field_confidence: 0.93)
```

### Example 4 — source_record_id 571a3fb647cda1d6
RAW
```
Trading Name: ADPA Ltd
Outlet Name: ADPAQ
Website: http://adpa.com.au
Outlet Address: 29 Mary St
Outlet Suburb: GYMPIE
Outlet Postcode: 4570
Telephone Number: (07) 5482 2180
Online Mail Order Flag: No
Australia Wide Flag: Yes
Overseas Flag: No
Senior Scheme Flag: Yes
Carer Scheme Flag: Yes
Business Category: Dental Prosthetists
Discount: Complimentary consultation for denture assessment.
Latitude: -26.18987
Longitude: 152.66159
Mobile Business Flag: No
Parent Business Category: Health and Medical
```
CANONICAL
```
entity.trading_name = "ADPA Ltd"    (raw: "ADPA Ltd", field_confidence: 0.9)
entity.website = "http://adpa.com.au"    (raw: "http://adpa.com.au", field_confidence: 0.8)
address.full = "29 Mary St"    (raw: "29 Mary St", field_confidence: 0.7)
address.locality = "GYMPIE"    (raw: "GYMPIE", field_confidence: 0.92)
address.postcode = "4570"    (raw: "4570", field_confidence: 0.93)
```

### Example 5 — source_record_id 450af831b5c638df
RAW
```
Trading Name: Andersens Floor Coverings
Outlet Name: Andersens Carpets
Website: http://www.andersens.com.au
Outlet Address: 60 Boat Harbour Dr
Outlet Suburb: HERVEY BAY
Outlet Postcode: 4655
Telephone Number: (07) 4124 3700
Online Mail Order Flag: No
Australia Wide Flag: Yes
Overseas Flag: Yes
Senior Scheme Flag: Yes
Carer Scheme Flag: Yes
Business Category: Carpets and Floor Coverings
Discount: 15% off ticketed price. Not valid with any other offer.
Latitude: -25.28592
Longitude: 152.82546
Mobile Business Flag: No
Parent Business Category: House and Home
```
CANONICAL
```
entity.trading_name = "Andersens Floor Coverings"    (raw: "Andersens Floor Coverings", field_confidence: 0.9)
entity.website = "http://www.andersens.com.au"    (raw: "http://www.andersens.com.au", field_confidence: 0.8)
address.full = "60 Boat Harbour Dr"    (raw: "60 Boat Harbour Dr", field_confidence: 0.7)
address.locality = "HERVEY BAY"    (raw: "HERVEY BAY", field_confidence: 0.92)
address.postcode = "4655"    (raw: "4655", field_confidence: 0.93)
```

## Your decision

Run exactly one of:

    firm onboard business-discount-directory --decide "approve"
    firm onboard business-discount-directory --decide "reject: <what is wrong and what to use instead>"
    firm onboard business-discount-directory --decide "abandon"

You never edit the config directly — a hand-edited config is hand-authored, and
the point is that it is not. Reject with a comment instead.