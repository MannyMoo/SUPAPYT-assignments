#!/usr/bin/env python3

from Database import Database
from datetime import datetime
from collections import Counter
from math import floor

db = Database()
with open('../GEM-GHEC-v1.txt') as finput :
    db.read_from_csv((line for line in finput if not line.startswith('#')),
                     True, delimiter = '\t')

print_prob = lambda n : print('*' * 10, 'Prob', n, '*' * 10)

# 1)
print_prob(1)
magmin = db.min('M')
magmax = db.max('M')

print('Smallest:')
for entry in db.filter(lambda entry : entry.M == magmin) :
    print(entry)
print()
print('Largest:')
for entry in db.filter(lambda entry : entry.M == magmax) :
    print(entry)
print()

# 2)
print_prob(2)
def try_int(val) :
    try :
        return int(val)
    except :
        return 0
    
db.sort(lambda entry : datetime(year = try_int(entry.Year),
                                month = max(try_int(entry.Mo), 1),
                                day = max(try_int(entry.Da), 1),
                                hour = try_int(entry.Ho),
                                minute = try_int(entry.Mi),
                                second = try_int(entry.Se)))
print('Earliest:')
earliest = db[0]
print(earliest)
print('Latest:')
latest = db[-1]
print(latest)
                                
# 3)
print_prob(3)

print('Magnitude:')
db.print_stats('M', form = '5.2f')
print('Depth [km]:')
db.print_stats('Dep', form = '5.2f')

# 4)
print_prob(4)
floor_div = lambda val, div : int(floor(val/div)*div)

decadecount = Counter(floor_div(entry.Year, 10.) for entry in db)
for decade in range(floor_div(earliest.Year, 10.), floor_div(latest.Year, 10.) + 10, 10) :
    print(decade, decadecount.get(decade, 0))

# # 5)
# print_prob(5)
# for period in range(floor_div(earliest.Year, 50), floor_div(latest.Year, 50) + 50, 50) :
#     perioddb = db.filter(lambda entry : floor_div(entry.Year, 50) == period)
#     print(period, '-', period + 50)
#     perioddb.print_stats('M', form = '5.2f')

# 5)
print_prob(5)
areacount = Counter(floor_div(lon, 10.) for lon in db.iterator('Lon'))
for lon in range(-180, 180, 10) :
    print('{0:4d} - {1:4d}: {2}'.format(lon, lon+10, areacount.get(lon, 0)))
maxarea, maxcount = max(areacount.items(), key = lambda v : v[1])
print('Most active area:', maxarea, '-', maxarea + 10, ':', maxcount)
