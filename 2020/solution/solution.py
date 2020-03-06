'''Solve the SUPAPYT assignment.'''

from collections import Counter
from datetime import datetime
from math import floor

def problem1(db):
    '''1) The names of the objects with the smallest and largest minimum orbit
    intersection distance (MOID) to Earth (the "moid" column). Not all entries
    have a "moid" value - those without one should be ignored.'''

    print('Problem 1:')
    minentry = db.min_entry('moid')
    maxentry = db.max_entry('moid')
    print('Entry with min. MOID to Earth: {0:20}, MOID: {1:5.3g}'.format(minentry.full_name.strip(), minentry.moid))
    print('Entry with max. MOID to Earth: {0:20}, MOID: {1:5.3g}'.format(maxentry.full_name.strip(), maxentry.moid))
    print()
    
def problem2(db):
    '''2) The mean and standard deviation of the diameters of the objects 
    (the "diameter" column).'''

    print('Problem 2:')
    print('Diameter stats:')
    db.print_stats('diameter', '5.3g')
    print()
    
def problem3(db):
    '''3) The min, max, mean and standard deviation of the MOID to Earth 
    for objects with the Near-Earth Object flag = Y ("neo" column), and 
    for objects with the Potentially Hazardous Asteroid flag = Y ("pha" column).'''
    
    print('Problem 3:')
    print('MOID to Earth stats, NEO = Y:')
    db.filter_matching('neo', 'Y').print_stats('moid', '5.3g')
    print()
    print('MOID to Earth stats, PHA = Y:')
    db.filter_matching('pha', 'Y').print_stats('moid', '5.3g')
    print()

def problem4(db):
    '''4) How many objects have been found by each person/institution ("producer" column).'''

    print('Problem 4:')
    counter = Counter(db.non_null_iterator('producer'))
    print('Number of objects per person/institution:')
    sortedlist = sorted(counter.items(), key = lambda x : x[1])
    for name, n in sortedlist:
        print(name.ljust(25), n)
    print()

def problem5(db):
    '''5) The names of the objects with the earliest and latest first observation 
    ("first_obs" column).'''

    print('Problem 5:')
    earliest = db.min_entry('first_obs')
    latest = db.max_entry('first_obs')
    print('Earliest: {0:20} {1}'.format(earliest.full_name.strip(), earliest.first_obs))
    print('Latest:   {0:20} {1}'.format(latest.full_name.strip(), latest.first_obs))
    print()
    
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

    mindecade = first_obs_decade(db.min_entry('first_obs'))
    maxdecade = first_obs_decade(db.max_entry('first_obs'))
    magdb = db.filter(lambda entry : entry.H)
    print('Mean magnitudes per decade:')
    for decade in range(mindecade, maxdecade+10, 10):
        decadedb = magdb.filter(lambda entry : (first_obs_decade(entry) == decade))
        if not decadedb:
            continue
        meanmag = decadedb.mean('H')
        meanmoid = decadedb.mean('moid')
        print(f'{decade}: H: {meanmag:5.3g} MOID: {meanmoid:5.3g}')
        
        #print(decade)
        #decadedb.print_stats('H', '5.3g')
        #print()
        
    print()

def main():
    '''Execute the functions to solve the problems.'''
    from Database import Database

    db = Database()
    with open('small-body-db.csv') as finput:
        db.read_from_csv(finput, True)

    problem1(db)
    problem2(db)
    problem3(db)
    problem4(db)
    problem5(db)
    problem6(db)
    
if __name__ == '__main__':
    main()

