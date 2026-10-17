# Mapping review — business-discount-directory

| | |
|---|---|
| Dataset | business-discount-directory — Business Discount Directory |
| Publisher / licence | Customer Services, Open Data and Small and Family Business / CC-BY-4.0 |
| Resource | https://www.data.qld.gov.au/dataset/fac8c9a4-03d5-44c6-9a9e-bb81085b0a44/resource/33159533-c2ee-4e11-902d-e2d250e2c84c/download/opendata-discount-offers-20260917170016.csv |
| Reader | {"format": "csv", "delimiter": ",", "encoding": "utf-8-sig", "header_row": 0, "sheet": null} |
| Agent run | revisions used 1/3 · steps 8 |
| **Status** | **PASSING WITH FLAGS** |
| Source reliability | 0.6 — A state government directory of businesses that self-register for the discount schemes: official and curated, but the contact and business details are supplied by the businesses themselves and not verified against a register, and it carries no ABN or ACN. |
| Record id | row_hash [] — The source has no record key, and no ABN or ACN either. Trading Name has 84 distinct values and Outlet Name 109 across 200 rows, so neither is unique. Telephone Number has 172 distinct values, and Outlet Address has 161 distinct values with 11% nulls, so neither is unique either. No plausible composite is shown to be unique over the full sample, so row_hash is the safe choice. |
| Observed at | dataset_modified → 2026-09-24 (basis: proxy) — The file has no per-record extract or last-updated date column. The only dated information is the catalogue modified date, so dataset_modified is used as a weak proxy. |

## Mapping (6 field mappings from 18 source columns)

| canonical | ← source column | transforms | conf. | cond. | evidence |
|---|---|---|---|---|---|
| entity.trading_name | Trading Name | `["trim", "empty_to_null"]` | 0.85 |  | Column 'Trading Name' holds values like 'Amplifon', 'Andersens Floor Coverings' and 'Access Dental Services Pty Ltd'. These are the names the businesses trade under in the discount directory, repeated across their outlet |
| entity.trading_name | Outlet Name | `["trim", "empty_to_null"]` | 0.7 |  | Column 'Outlet Name' holds outlet-level labels such as 'Amplifon Mackay', 'ADPAQ' and 'Allcracft Sewing Machines' (a typo of the trading name). Per the reviewer, the ontology allows multiple trading names, one observatio |
| entity.website | Website | `["trim", "empty_to_null", "url_normalize"]` | 0.8 |  | Column 'Website' holds values like 'http://www.andersens.com.au', 'http://adpa.com.au' and 'https://andrewsairportpark.com.au'. They are the business's web address. Some are malformed at source, e.g. 'http://https://www. |
| address.full | Outlet Address | `["trim", "empty_to_null"]` | 0.6 |  | Column 'Outlet Address' holds values like '10 Herberton St', '179 Nicklin Way' and 'Shop 124, Mount Pleasant Shopping Centre', but the values are often shopping-centre or venue names rather than street addresses, e.g. 'C |
| address.locality | Outlet Suburb | `["trim", "empty_to_null"]` | 0.92 |  | Column 'Outlet Suburb' holds values like 'MACKAY', 'TWEED HEADS SOUTH' and 'MAROOCHYDORE'. These are suburb or town names of the outlet, so address.locality. The rest of the address is in separate columns. |
| address.postcode | Outlet Postcode | `["trim", "empty_to_null", "postcode_normalize"]` | 0.93 |  | Column 'Outlet Postcode' holds values like '4740', '2486' and '3216'. They are all 4-digit Australian postcodes of the outlet. postcode_normalize zero-pads any that lost a leading zero. |

## Validation — 350 held-out rows (loop set; final acceptance runs once after approval)

| check | threshold | result | pass |
|---|---|---|---|
| null drift (entity.trading_name ← Trading Name) | <= +2pp | +0.0% | ✅ |
| null drift (entity.trading_name ← Outlet Name) | <= +2pp | +0.0% | ✅ |
| null drift (entity.website ← Website) | <= +2pp | -0.0% | ✅ |
| null drift (address.full ← Outlet Address) | <= +2pp | +0.0% | ✅ |
| null drift (address.locality ← Outlet Suburb) | <= +2pp | +0.0% | ✅ |
| null drift (address.postcode ← Outlet Postcode) | <= +2pp | +0.0% | ✅ |
| record_id effectively unique (full sample) | <= 0.5% duplicates | 1 duplicates (0.29%) | ✅ |
| minimum useful (a name or an identifier mapped) | required | yes | ✅ |

### Failing examples
none

## Semantic spot-check — 10 held-out records: 49 ok, 9 suspicious

| record | field | verdict | why |
|---|---|---|---|
| a8ad7ecfb0ece669 | entity.trading_name | ok | 'Amplifon' is a brand trading name copied verbatim from the Trading Name column. |
| a8ad7ecfb0ece669 | entity.trading_name | suspicious | 'Amplifon Cleveland' is a brand plus location label for one outlet, not a name the business trades under, so Outlet Name may not mean trading_name. |
| a8ad7ecfb0ece669 | entity.website | suspicious | The canonical value ends in '...AUORG1PKAVT6A00', but the raw cell ends at '...AUORG1PKAVT', so the output has text the source lacks. It also keeps the malforme |
| a8ad7ecfb0ece669 | address.full | ok | 'U 4, 107-111 Queen St' is a genuine street address for the outlet, copied verbatim. |
| a8ad7ecfb0ece669 | address.locality | ok | CLEVELAND is a suburb name and matches postcode 4163. |
| a8ad7ecfb0ece669 | address.postcode | ok | 4163 is a valid Cleveland QLD postcode, copied verbatim. |
| 3373db45d8d72436 | entity.trading_name | ok | 'Angus & Coote' is the brand trading name. |
| 3373db45d8d72436 | entity.trading_name | ok | Outlet Name is the same brand name, so this is a valid trading name but a duplicate observation. |
| 3373db45d8d72436 | entity.website | ok | This is the brand's website, copied verbatim. |
| 3373db45d8d72436 | address.full | suspicious | 'Castletown Shp Cnt' is a shopping-centre name with no street address, so it is a venue label rather than an address. |
| 3373db45d8d72436 | address.locality | ok | HYDE PARK is a suburb (Townsville) and fits postcode 4812. |
| 3373db45d8d72436 | address.postcode | ok | 4812 is a plausible QLD postcode and matches the suburb. |
| 414de081d51ecd99 | entity.trading_name | ok | This is the brand trading name. |
| 414de081d51ecd99 | entity.trading_name | ok | Outlet Name is identical to the brand name, so it is valid but a duplicate. |
| 414de081d51ecd99 | entity.website | ok | This is the brand's website, copied verbatim. |
| 414de081d51ecd99 | address.full | suspicious | 'Central Highlands Market Place' is a venue name with no street number or street, so it is not a street address. |
| 414de081d51ecd99 | address.locality | ok | EMERALD is a QLD town and fits postcode 4720. |
| 414de081d51ecd99 | address.postcode | ok | 4720 matches Emerald. |
| f8f6df06cafb6d3b | entity.trading_name | ok | 'Andersens Floor Coverings' is the brand trading name. |
| f8f6df06cafb6d3b | entity.trading_name | ok | 'Andersens Carpets' is a plausible alternate trading name for the outlet. |
| f8f6df06cafb6d3b | entity.website | ok | This is the brand's website, copied verbatim. |
| f8f6df06cafb6d3b | address.full | ok | '36 Duke St' is a real street address. |
| f8f6df06cafb6d3b | address.locality | ok | GYMPIE is a suburb/town and fits postcode 4570. |
| f8f6df06cafb6d3b | address.postcode | ok | 4570 matches Gympie. |
| 9bf76a92aa7e1a75 | entity.trading_name | ok | 'Aksa Home Decor' is a trading-style name. |
| 9bf76a92aa7e1a75 | entity.trading_name | ok | Outlet Name is identical to Trading Name, so this is a duplicate observation. |
| 9bf76a92aa7e1a75 | entity.website | ok | This is the business's own website, copied verbatim. |
| 9bf76a92aa7e1a75 | address.locality | ok | KILLARA is a Sydney suburb and fits postcode 2071. The business is an online or mobile operator with no street address. |
| 9bf76a92aa7e1a75 | address.postcode | ok | 2071 matches Killara NSW. |
| f9aad4867a42037c | entity.trading_name | ok | This is the brand trading name. |
| f9aad4867a42037c | entity.trading_name | ok | 'Andersens Carpets' is a plausible alternate trading name. |
| f9aad4867a42037c | entity.website | ok | This is the brand's website, copied verbatim. |
| f9aad4867a42037c | address.full | ok | This is a street address. The source's double space (where a comma was likely dropped) became a single space, giving 'Shop 4 1 Greenway Dr', which is slightly a |
| f9aad4867a42037c | address.locality | ok | TWEED HEADS is a suburb and fits postcode 2485. |
| f9aad4867a42037c | address.postcode | ok | 2485 matches Tweed Heads NSW. |
| ab772061675d9a9d | entity.trading_name | ok | 'Arthurs Autoglass' is a trading name. |
| ab772061675d9a9d | entity.trading_name | ok | 'Morayfield Discount Autoglass' is a distinct outlet-level trading style. It is acceptable as a second trading name, but it differs from the brand name. |
| ab772061675d9a9d | entity.website | ok | This is an outlet-specific site, copied verbatim, and consistent with the outlet name. |
| ab772061675d9a9d | address.full | ok | '125 Morayfield Rd' is a street address. |
| ab772061675d9a9d | address.locality | ok | CABOOLTURE SOUTH is a suburb and fits postcode 4510. |
| ab772061675d9a9d | address.postcode | ok | 4510 matches the Caboolture area. |
| 8797e54e37a80189 | entity.trading_name | suspicious | 'ADPA Ltd' carries a company suffix and looks like a registered or association name rather than a trading name, so it may belong in legal_name. |
| 8797e54e37a80189 | entity.trading_name | ok | 'ADPAQ' is an abbreviated outlet label, likely the Queensland branch, and is plausible as a trading name. |
| 8797e54e37a80189 | entity.website | ok | This is the organisation's website, copied verbatim. |
| 8797e54e37a80189 | address.full | ok | This is a shop and street address. The double space became a single space, which is fine. |
| 8797e54e37a80189 | address.locality | ok | ROBINA is a Gold Coast suburb and fits postcode 4226. |
| 8797e54e37a80189 | address.postcode | ok | 4226 matches Robina. |
| 86f9d51258089cb6 | entity.trading_name | suspicious | 'Ali Baba Lebanese Cuisine Pty Ltd' includes a company suffix, so it looks like a registered name rather than a trading name. |
| 86f9d51258089cb6 | entity.trading_name | suspicious | Outlet Name repeats the same Pty Ltd registered-style name. The suffix suggests a legal name in a trading_name field, and the claim is a duplicate. |
| 86f9d51258089cb6 | address.full | suspicious | 'Sunshine Plaza' is a shopping-centre name with no street address. |
| 86f9d51258089cb6 | address.locality | ok | MAROOCHYDORE is a suburb and fits postcode 4558. |
| 86f9d51258089cb6 | address.postcode | ok | 4558 matches Maroochydore. |
| 7655e30afe549885 | entity.trading_name | ok | This is the brand trading name. |
| 7655e30afe549885 | entity.trading_name | ok | Outlet Name is identical to the brand name, so this is a valid duplicate. |
| 7655e30afe549885 | entity.website | ok | This is the brand's website, copied verbatim. |
| 7655e30afe549885 | address.full | suspicious | 'Caneland Central Shp Cnt' is a shopping-centre name with no street address. |
| 7655e30afe549885 | address.locality | ok | MACKAY is a city and fits postcode 4740. |
| 7655e30afe549885 | address.postcode | ok | 4740 matches Mackay. |

Notes: The website claim on record a8ad7ecfb0ece669 contains characters ('6A00') absent from the raw cell, so the output does not faithfully reflect the source. The transform or extraction pipeline should be checked.; The address.full mapping often captures shopping-centre or venue names rather than street addresses (Castletown Shp Cnt, Central Highlands Market Place, Sunshine Plaza, Caneland Central Shp Cnt). The field's meaning is inconsistent across rows.; Trading Name and Outlet Name are both mapped to entity.trading_name, so many rows emit duplicate identical observations.; Some trading_name values carry company suffixes (ADPA Ltd, Ali Baba Lebanese Cuisine Pty Ltd) and are probably registered names. Location-suffixed outlet labels such as 'Amplifon Cleveland' are not true trading names.; No address.state claim is produced although every row is Australian. State could be derived from postcode or lat/long but is not mapped.; No legal_name, ABN or status is mapped. This is appropriate because the source is a discount directory, but it means the source gives no registered-entity identity.

## Unmapped columns (12)

| source column | reason |
|---|---|
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
entity.trading_name = "Andersens Floor Coverings"    (raw: "Andersens Floor Coverings", field_confidence: 0.85)
entity.trading_name = "Andersens Carpets"    (raw: "Andersens Carpets", field_confidence: 0.7)
entity.website = "http://www.andersens.com.au"    (raw: "http://www.andersens.com.au", field_confidence: 0.8)
address.full = "36 Brisbane Rd"    (raw: "36 Brisbane Rd", field_confidence: 0.6)
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
entity.trading_name = "Andersens Floor Coverings"    (raw: "Andersens Floor Coverings", field_confidence: 0.85)
entity.trading_name = "Andersens Carpets"    (raw: "Andersens Carpets", field_confidence: 0.7)
entity.website = "http://www.andersens.com.au"    (raw: "http://www.andersens.com.au", field_confidence: 0.8)
address.full = "17 Mabel St"    (raw: "17 Mabel St", field_confidence: 0.6)
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
entity.trading_name = "ADPA Ltd"    (raw: "ADPA Ltd", field_confidence: 0.85)
entity.trading_name = "ADPAQ"    (raw: "ADPAQ", field_confidence: 0.7)
entity.website = "http://adpa.com.au"    (raw: "http://adpa.com.au", field_confidence: 0.8)
address.full = "U 9 521 Beams Rd"    (raw: "U 9  521 Beams Rd", field_confidence: 0.6)
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
entity.trading_name = "ADPA Ltd"    (raw: "ADPA Ltd", field_confidence: 0.85)
entity.trading_name = "ADPAQ"    (raw: "ADPAQ", field_confidence: 0.7)
entity.website = "http://adpa.com.au"    (raw: "http://adpa.com.au", field_confidence: 0.8)
address.full = "29 Mary St"    (raw: "29 Mary St", field_confidence: 0.6)
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
entity.trading_name = "Andersens Floor Coverings"    (raw: "Andersens Floor Coverings", field_confidence: 0.85)
entity.trading_name = "Andersens Carpets"    (raw: "Andersens Carpets", field_confidence: 0.7)
entity.website = "http://www.andersens.com.au"    (raw: "http://www.andersens.com.au", field_confidence: 0.8)
address.full = "60 Boat Harbour Dr"    (raw: "60 Boat Harbour Dr", field_confidence: 0.6)
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