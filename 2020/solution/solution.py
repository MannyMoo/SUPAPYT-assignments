'''Solve the SUPAPYT assignment.'''

from collections import Counter, defaultdict
from datetime import datetime
from math import floor
from Database import Database

def problem1(db):
    '''1) The names of the objects with the smallest and largest minimum orbit
    intersection distance (MOID) to Earth (the "moid" column). Not all entries
    have a "moid" value - those without one should be ignored.'''

    minentry = db.min_entry('moid')
    maxentry = db.max_entry('moid')
    print('Entry with min. MOID to Earth: {0:20}, MOID: {1:5.3g}'.format(minentry.full_name.strip(), minentry.moid))
    print('Entry with max. MOID to Earth: {0:20}, MOID: {1:5.3g}'.format(maxentry.full_name.strip(), maxentry.moid))
    
def problem2(db):
    '''2) The mean and standard deviation of the diameters of the objects 
    (the "diameter" column).'''

    print('Diameter stats:')
    db.print_stats('diameter', '5.3g')
    
def problem3(db):
    '''3) The min, max, mean and standard deviation of the MOID to Earth 
    for objects with the Near-Earth Object flag = Y ("neo" column), and 
    for objects with the Potentially Hazardous Asteroid flag = Y ("pha" column).'''
    
    print('MOID to Earth stats, NEO = Y:')
    db.filter_matching('neo', 'Y').print_stats('moid', '5.3g')
    print()
    print('MOID to Earth stats, PHA = Y:')
    db.filter_matching('pha', 'Y').print_stats('moid', '5.3g')

def problem4(db):
    '''4) How many objects have been found by each person/institution ("producer" column).'''

    counter = Counter(db.non_null_iterator('producer'))
    print('Number of objects per person/institution:')
    sortedlist = sorted(counter.items(), key = lambda x : x[1])
    for name, n in sortedlist:
        print(name.ljust(25), n)

def problem5(db):
    '''5) The names of the objects with the earliest and latest first observation 
    ("first_obs" column).'''

    earliest = db.min_entry('first_obs')
    latest = db.max_entry('first_obs')
    print('Earliest: {0:20} {1}'.format(earliest.full_name.strip(), earliest.first_obs))
    print('Latest:   {0:20} {1}'.format(latest.full_name.strip(), latest.first_obs))
    
def first_obs_date(entry):
    '''Get the first observation date of the entry as a datetime instance.'''
    for form in '%Y-%m-%d', '%Y-%m-??', '%Y-??-??':
        try:
            return datetime.strptime(entry.first_obs, form)
        except ValueError:
            continue
    raise ValueError('Failed to parse first observation date:', repr(entry.first_obs))

def first_obs_decade(entry):
    '''Get the decade of the first observation for the given entry.'''
    
    firstobs = first_obs_date(entry)
    decade = int(floor(firstobs.year/10.) * 10)
    return decade

def problem6(db):
    '''6) The mean absolute magnitude ("H") of objects with first observation
    in each decade (group the objects according to the decade of their first
    observation and calculate the mean "H" for each group). A decade is defined
    as, eg, 2000-01-01 to 2009-12-31 inclusive.'''

    # Get the DB of entries that have H values
    magdb = db.filter(lambda entry : entry.H)
    # Sort the entries according to their first observation decade.
    decadedbs = defaultdict(Database)
    for entry in magdb:
        decadedbs[first_obs_decade(entry)].entries.append(entry)
    # Get the range of decades.
    mindecade = min(decadedbs)
    maxdecade = max(decadedbs)

    # Loop over decades.
    print('Mean magnitudes per decade:')    
    for decade in range(mindecade, maxdecade+10, 10):
        # No entries for this decade
        if not decade in decadedbs:
            print(f'{decade}: -')
            continue
        # Get the DB for this decade & its mean H
        decadedb = decadedbs[decade]
        meanmag = decadedb.mean('H')
        meanmoid = decadedb.mean('moid')
        print(f'{decade}: H: {meanmag:5.3g} MOID: {meanmoid:5.3g}')
        
def main():
    '''Execute the functions to solve the problems.'''

    db = Database()
    with open('small-body-db.csv') as finput:
        db.read_from_csv(finput, True)

    for prob in problem1, problem2, problem3, problem4, problem5, problem6:
        print('*** ' + prob.__doc__)
        print()
        prob(db)
        print()
    return db

if __name__ == '__main__':
    db = main()

