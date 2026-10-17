# Part 1 hand-check evidence

## 1. Dept. of Justice Annual Report Registered Training Organisations 2013-14
- no machine-readable resource (formats: ['XLS'])

## 2. ACNC 2020 Annual Information Statement (AIS) Data
- resource: CSV, https://data.gov.au/data/dataset/28a94374-d516-4200-a6f8-c09e76f58cc5/resource/62c7b3d3-4358-4d57-b810-a36732d36e2d/download/datadotgov_ais20.csv
- columns (93): ['abn', 'charity name', 'registration status', 'charity website', 'charity size', 'basic religious charity', 'ais due date', 'date ais received', 'financial report date received', 'conducted activities', 'why charity did not conduct activities', 'international activities details']
- sample row: ['11000047950', 'Sydney Missionary & Bible Coll', 'Registered', 'www.smbc.edu.au', 'Large', 'n', '30/06/2021', '08/06/2021']
- sample row: ['11000073870', 'Integricare Limited', 'Registered', 'www.integricare.org.au', 'Large', 'n', '31/01/2021', '29/01/2021']
- entity signals: name→charity name, charity→charity name, entity→report consolidated with more than one entity, abn→abn

## 3. Corporate Tax Transparency
- resource: XLSX, https://data.gov.au/data/dataset/c2524c87-cea4-4636-acac-599a82048a26/resource/15bf4eaa-7a14-48e9-8a3f-092df32a644e/download/2024-25-corporate-report-of-entity-tax-information.xlsx
- columns (6): ['Name', 'ABN', 'Total income $', 'Taxable income $', 'Tax payable $', 'Income year']
- sample row: ['1 MENDS STREET PTY LTD', '94600082111', '108996236', '10603699', '3181110', '2024-25']
- sample row: ['1884 PTY LIMITED', '83114980880', '319135614', '18129064', '5438719', '2024-25']
- entity signals: name→name, abn→abn

## 4. ASIC - Australian Financial Services Licensee Dataset
- resource: CSV, https://data.gov.au/data/dataset/ab7eddce-84df-4098-bc8f-500d0d9776d1/resource/d98a113d-6b50-40e6-b65f-2612efc877f4/download/afs_lic_202610.csv
- columns (11): ['REGISTER_NAME', 'AFS_LIC_NUM', 'AFS_LIC_NAME', 'AFS_LIC_ABN_ACN', 'AFS_LIC_START_DT', 'AFS_LIC_PRE_FSR', 'AFS_LIC_ADD_LOCAL', 'AFS_LIC_ADD_STATE', 'AFS_LIC_ADD_PCODE', 'AFS_LIC_ADD_COUNTRY', 'AFS_LIC_CONDITION']
- sample row: ['AFS Licence', '218600', 'IPIB PTY LTD', '85007186003', '02/05/2002', '"General insurance broker","00', 'SOUTHBANK', 'VIC']
- sample row: ['AFS Licence', '218678', 'IMC PACIFIC PTY LTD', '89099273846', '26/04/2002', '', 'SYDNEY', 'NSW']
- entity signals: name→register_name, abn→afs_lic_abn_acn, acn→afs_lic_abn_acn, lic_num→afs_lic_num

## 5. ACNC 2016 Annual Information Statement Data
- resource: XLSX, https://data.gov.au/data/dataset/7e073d71-4eef-4f0c-921b-9880fb59b206/resource/b4a08924-af4f-4def-96f7-bf32ada7ee2b/download/datadotgov_ais16.xlsx
- columns (138): ['ABN', 'Charity Name', 'Other Organisation Names', 'Registration Status', 'Address_Type', 'Address Line 1', 'Address Line 2', 'Town/City', 'State', 'Postcode', 'Country', 'Charity Size']
- sample row: ['11000047950', 'Sydney Missionary & Bible Coll', '', 'Registered', 'Business', '43 Badminton Road', '', 'Croydon']
- sample row: ['11000073870', 'Integricare Limited', '', 'Registered', 'Business', 'Suite 1.02, Level 1, Quad 3', '102 Bennelong Parkway', 'Sydney Olympic Park']
- entity signals: name→charity name, organisation→other organisation names, charity→charity name, entity→is financial report consolidated with more than one entity?, abn→abn

## 6. ACNC 2015 Annual Information Statement Data
- FETCH FAILED: xlsx too big to fetch here (31877585 bytes)

## 7. ACNC 2021 Annual Information Statement (AIS) Data
- resource: CSV, https://data.gov.au/data/dataset/db8def1b-b3ba-4536-98eb-60c99e5495e5/resource/bbb19fa5-2f63-49cb-96b2-523e25828f27/download/datadotgov_ais21.csv
- columns (93): ['abn', 'charity name', 'registration status', 'charity website', 'charity size', 'basic religious charity', 'ais due date', 'date ais received', 'financial report date received', 'conducted activities', 'why charity did not conduct activities', 'international activities details']
- sample row: ['11000047950', 'Sydney Missionary & Bible Coll', 'Registered', 'www.smbc.edu.au', 'Large', 'n', '30/06/2022', '20/06/2022']
- sample row: ['11000073870', 'Integricare Limited', 'Registered', 'www.integricare.org.au', 'Large', 'n', '31/01/2022', '26/04/2022']
- entity signals: name→charity name, charity→charity name, entity→report consolidated with more than one entity, abn→abn

## 8. ACNC 2019 Annual Information Statement Data
- resource: CSV, https://data.gov.au/data/dataset/34b35c52-8af0-4cc1-aa0b-2278f6416d09/resource/76006467-18f2-4094-a1cb-50544fd9b7b2/download/datadotgov_ais19.csv
- columns (167): ['abn', 'charity name', 'other organisation names', 'Registration Status', 'address line 1', 'address line 2', 'town/city', 'state', 'postcode', 'country', 'charity size', 'basic religious charity']
- sample row: ['11000047950', 'Sydney Missionary & Bible Coll', '', 'Registered', '43 Badminton Rd', '', 'Croydon', 'New South Wales']
- sample row: ['11000073870', 'Integricare Limited', '', 'Registered', 'Se 3 102 Bennelong Pkwy', '', 'Sydney Olympic Park', 'New South Wales']
- entity signals: name→charity name, organisation→other organisation names, charity→charity name, entity→report consolidated with more than one entity, abn→abn

## 9. Northern Territory Groundwater Management Units 20140630
- no machine-readable resource (formats: ['ZIP'])

## 10. ACNC 2018 Annual Information Statement Data
- resource: XLSX, https://data.gov.au/data/dataset/cfc1a18e-f4e0-4ed8-9a19-36b59b7a3d5b/resource/dbba5286-8a92-4ec9-8733-04375275d93a/download/2018-ais_list-of-group-members.xlsx
- columns (17): ['account:CWZQGwr0W5hv1wagOSlycQhNDikeKVSZ/xfxeY/DEmwqbHUcfekurC6vppeAGRuZubssy5aHIquVIa/IRrTgaw==:accountid=%28Do%20Not%20Modify%29%20Account&checksumLogicalName=%28Do%20Not%20Modify%29%20Row%20Checksum&modifiedon=%28Do%20Not%20Modify%29%20Modified%20On&parentaccountid=Parent%20Account&acnc_abn=ABN&name=Legal%20Name&acnc_groupstartdate=Group%20Start%20Date&acnc_groupenddate=Group%20End%20Date&statuscode=Charity%20Status', '', '', '', '', '', '', '', '', '', '', '']
- sample row: ['Registered', 'Pending', 'Revoked ABN', 'Revoked Double Defaulter', 'Revoked RTS', 'Revoked Registration', 'Revoked Compliance', 'Voluntarily Revoked Merged']
- entity signals: name→account:cwzqgwr0w5hv1wagoslycqhndikekvsz/xfxey/demwqbhucfekurc6vppeagruzubssy5ahiquvia/irrtgaw==:accountid=%28do%20not%20modify%29%20account&checksumlogicalname=%28do%20not%20modify%29%20row%20checksum&modifiedon=%28do%20not%20modify%29%20modified%20on&parentaccountid=parent%20account&acnc_abn=abn&name=legal%20name&acnc_groupstartdate=group%20start%20date&acnc_groupenddate=group%20end%20date&statuscode=charity%20status, charity→account:cwzqgwr0w5hv1wagoslycqhndikekvsz/xfxey/demwqbhucfekurc6vppeagruzubssy5ahiquvia/irrtgaw==:accountid=%28do%20not%20modify%29%20account&checksumlogicalname=%28do%20not%20modify%29%20row%20checksum&modifiedon=%28do%20not%20modify%29%20modified%20on&parentaccountid=parent%20account&acnc_abn=abn&name=legal%20name&acnc_groupstartdate=group%20start%20date&acnc_groupenddate=group%20end%20date&statuscode=charity%20status, abn→account:cwzqgwr0w5hv1wagoslycqhndikekvsz/xfxey/demwqbhucfekurc6vppeagruzubssy5ahiquvia/irrtgaw==:accountid=%28do%20not%20modify%29%20account&checksumlogicalname=%28do%20not%20modify%29%20row%20checksum&modifiedon=%28do%20not%20modify%29%20modified%20on&parentaccountid=parent%20account&acnc_abn=abn&name=legal%20name&acnc_groupstartdate=group%20start%20date&acnc_groupenddate=group%20end%20date&statuscode=charity%20status, acn→account:cwzqgwr0w5hv1wagoslycqhndikekvsz/xfxey/demwqbhucfekurc6vppeagruzubssy5ahiquvia/irrtgaw==:accountid=%28do%20not%20modify%29%20account&checksumlogicalname=%28do%20not%20modify%29%20row%20checksum&modifiedon=%28do%20not%20modify%29%20modified%20on&parentaccountid=parent%20account&acnc_abn=abn&name=legal%20name&acnc_groupstartdate=group%20start%20date&acnc_groupenddate=group%20end%20date&statuscode=charity%20status

## 11. APVMA PUBCRIS dataset for registered Agricultural and Veterinary Chemical Products and Approved Actives
- resource: CSV, https://data.gov.au/data/dataset/0de37904-43e0-4814-b21b-5b64fafefe6f/resource/a83d500d-b47a-4f03-9d77-4c0524217855/download/labelreg.csv
- columns (3): ['pcode', 'regno', 'regdate']
- sample row: ['38975', '0400', '17/05/2000 12:00:00 AM']
- sample row: ['38975', '0498', '30/03/1998 12:00:00 AM']
- entity signals: none

## 12. National Public Toilet Map
- resource: CSV, https://data.gov.au/data/dataset/553b3049-2b8b-46a2-95e6-640d7986a8c1/resource/34076296-6692-4e30-b627-67b7c4eb1027/download/toiletmapexport_261001_074429.csv
- columns (47): ['FacilityID', 'URL', 'Name', 'FacilityType', 'Address1', 'Town', 'State', 'AddressNote', 'Latitude', 'Longitude', 'Parking', 'ParkingAccessible']
- sample row: ['1', 'https://toiletmap.gov.au/facil', 'Sandy Beach Reserve', 'Park or reserve', 'Lost 15525, West Road', 'Bassendean', 'WA', '']
- sample row: ['2', 'https://toiletmap.gov.au/facil', 'Point Reserve', 'Park or reserve', 'Lot 197, North Road', 'Bassendean', 'WA', '']
- entity signals: name→name

## 13. Victorian Government Schools ABNs
- FETCH FAILED: Server disconnected without sending a response.

## 14. Register of Third-Party Lobbyists
- no machine-readable resource (formats: ['website link'])

## 15. P&SCO Projects Contract Disclosure Report 2024-25 Contractors Q4 April-June25
- FETCH FAILED: Client error '404 Not Found' for url 'https://www.data.qld.gov.au/dataset/4e883296-1dea-4d1d-9f1e-80c176692ac2/resource/62e8bae9-0881-4375-a8af-83315438f678/download/psco-portfolio-contract-disclosure-info-contractors-q4-april-to-june-25.csv'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404

## 16. ACNC 2014 Annual Information Statement data
- resource: XLSX, https://data.gov.au/data/dataset/d7992845-5d3b-4868-b012-71f672085412/resource/4d65259d-1ccf-4c78-a223-e2bd49dc5fb1/download/datadotgov_ais14.xlsx
- columns (153): ['ABN', 'AIS_Due_Date', 'Date_AIS_Received', 'Charity_Name', 'Other_Organisation_Names', 'Registration_Status', 'Address_Type', 'Address_Line_1', 'Address_Line_2', 'Town_City', 'State', 'Postcode']
- sample row: ['11000047950', '30/06/2015', '30/04/2015', 'Sydney Missionary & Bible Coll', '', 'Registered', 'Business', '43 Badminton Road']
- sample row: ['11000073870', '31/01/2015', '30/01/2015', 'Integricare Limited', '', 'Registered', 'Business', '2/23 Belmore St']
- entity signals: name→charity_name, organisation→other_organisation_names, charity→charity_name, abn→abn

## 17. Limousine and taxi service licence values – Queensland
- resource: CSV, https://www.data.qld.gov.au/dataset/abe00ded-8175-42cc-b054-3abd215f3eb8/resource/92e3c9f5-df8d-478d-9fec-bca7cd5838d6/download/20260630_limousine_service_licence_transfers.csv
- columns (2): ['TRANSFER (APPROVAL) DATE', ' TRANSFER PRICE ']
- sample row: ['27/08/2026', '1,000']
- sample row: ['29/06/2026', '']
- entity signals: none

## 18. ASIC - Banned and Disqualified Organisations Dataset
- resource: CSV, https://data.gov.au/data/dataset/a5fde808-ba32-4cee-bfcb-fbb3afa56a28/resource/ced03961-e6f7-4263-895a-0fd1d7996043/download/bd_org_202610.csv
- columns (8): ['REGISTER_NAME', 'BD_ORG_ACN', 'BD_ORG_NAME', 'BD_ORG_TYPE', 'BD_ORG_URL', 'BD_ORG_START_DT', 'BD_ORG_END_DT', 'BD_ORG_COMMENT']
- sample row: ['Banned and Disqualified Organi', '081402379', 'AUSTRALIAN BUSINESS INSURANCE ', 'Australian Financial Services ', 'Not available', '07/11/2006', '07/11/2008', 'No comment made']
- sample row: ['Banned and Disqualified Organi', '008876033', 'BLACKBURNE & DIXON PTY LTD', 'Credit banning by a State or T', 'http://asic.gov.au/online-serv', '10/04/2001', '', 'No comment made']
- entity signals: name→register_name, acn→bd_org_acn

## 19. ABN Lookup web services
- no machine-readable resource (formats: ['XML'])

## 20. New business registration transactions by service location
- resource: CSV, https://www.data.qld.gov.au/dataset/55d7cbdd-71bd-4f47-8948-66a4a26fbf17/resource/3dc50d30-944a-4b17-8a5d-8c29296e6bfe/download/20260407_new-business-registration-transactions-by-service-location.csv
- columns (7): ['��M\x00o\x00n\x00t\x00h\x00', '\x00S\x00u\x00b\x00u\x00r\x00b\x00', '\x00P\x00o\x00s\x00t\x00c\x00o\x00d\x00e\x00', '\x00T\x00r\x00a\x00n\x00s\x00a\x00c\x00t\x00i\x00o\x00n\x00 \x00T\x00y\x00p\x00e\x00', '\x00M\x00a\x00k\x00e\x00 \x00N\x00a\x00m\x00e\x00', '\x00M\x00o\x00d\x00e\x00l\x00 \x00N\x00a\x00m\x00e\x00', '\x00V\x00a\x00l\x00i\x00d\x00 \x00H\x00a\x00n\x00d\x00l\x00e\x00d\x00 \x00T\x00r\x00a\x00n\x00s\x00a\x00c\x00t\x00i\x00o\x00n\x00s\x00']
- sample row: ['\x000\x001\x00-\x000\x001\x00-\x002\x000\x002\x006\x00', '\x00A\x00C\x00A\x00C\x00I\x00A\x00 \x00R\x00I\x00D\x00G\x00E\x00', '\x004\x001\x001\x000\x00', '\x00R\x00e\x00g\x00i\x00s\x00t\x00r\x00a\x00t\x00i\x00o\x00n\x00 \x00N\x00e', '\x00A\x00R\x00B\x00 \x00T\x00O\x00Y\x00O\x00T\x00A\x00', '\x00L\x00A\x00N\x00D\x00C\x00R\x00U\x00I\x00S\x00E\x00R\x00', '\x002\x00']
- sample row: ['\x000\x001\x00-\x000\x001\x00-\x002\x000\x002\x006\x00', '\x00A\x00C\x00A\x00C\x00I\x00A\x00 \x00R\x00I\x00D\x00G\x00E\x00', '\x004\x001\x001\x000\x00', '\x00R\x00e\x00g\x00i\x00s\x00t\x00r\x00a\x00t\x00i\x00o\x00n\x00 \x00N\x00e', '\x00E\x00 \x00V\x00O\x00L\x00V\x00E\x00 \x00M\x00O\x00P\x00E\x00D\x00S\x00', "\x00R\x00O\x00L\x00L\x00'\x00N\x00 \x00F\x00R\x00E\x00E\x00D\x00O\x00M\x00", '\x001\x00']
- entity signals: none
