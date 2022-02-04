#!/usr/bin/env python3

'''Prepare C02 emissions data from World Bank for the assignment:
https://data.worldbank.org/indicator/EN.ATM.CO2E.PC?view=chart
'''

from Database import Database
from Database.Entry import class_factory

dbem = Database(csvfile='API_EN.ATM.CO2E.PC_DS2_en_csv_v2_3470453.csv')
dbmeta = Database(csvfile='Metadata_Country_API_EN.ATM.CO2E.PC_DS2_en_csv_v2_3470453.csv')

emattrs = list(dbem.Entry.attributes())
# Remove country code, indicator name, & indicator code
rmattrs = "Country Code","Indicator Name","Indicator Code","2019","2020",""
for attr in rmattrs:
    emattrs.remove(attr)
    
# Add Region & Income Group
addattrs = "Region", "IncomeGroup"
attrs = list(emattrs)
attrs[1:1] = list(addattrs)

Entry = class_factory(True, *attrs)

entries = []
for entry in dbem:
    vals = {attr : getattr(entry, attr) for attr in emattrs}
    # Remove contries with no data
    if not any(vals[str(i)] for i in range(1960, 2019)):
        continue
    metaentry = dbmeta.filter_matching('Country Code', getattr(entry, 'Country Code'))
    metaentry = list(metaentry)
    if not metaentry:
        print('Entry not found in metadata:')
        print(entry)
        print()
        continue
    ok = True
    for attr in addattrs:
        vals[attr] = getattr(metaentry[0], attr)
        ok = ok and vals[attr] != ''
    if not ok:
        continue
    entries.append(Entry(**vals))

dbout = Database(entries)
dbout.write_to_csv('PerCapitaC02Emissions.csv')
