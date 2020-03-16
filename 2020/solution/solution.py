#!/usr/bin/env python

'''Solve the SUPAPYT assignment, analysing a subset of the JPL small object database from 
https://ssd.jpl.nasa.gov/sbdb_query.cgi.'''

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

    # Some entries have ?? as the day or month try each of these in turn. The last one should
    # at least work.
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
    '''Parse the commandline arguments and execute the functions to solve the problems.'''

    # Annoylingly necessary to provide a custom usage as the default puts [--problems] before [fname].
    # Of course you can run it with, eg:
    # ./main.py --problems 1 2 -- <fname>
    # as well as
    # ./main.py <fname> --problems 1 2
    # but the default help doesn't point out that you need the "--" in the first instance.
    argparser = ArgumentParser(usage = 'main.py [-h] [fname] [--problems [PROBLEMS [PROBLEMS ...]]]')

    # Optional positional argument for the file name.
    argparser.add_argument('fname', nargs = '?', default = 'GEM-GHEC-v1.txt',
                           help = 'Name of the input file (default: GEM-GHEC-v1.txt)')
    # Optional named argument for the problems to execute. Can take any number
    # of values.
    problemnos = list(range(1,7))
    argparser.add_argument('--problems', nargs = '*', default = problemnos,
                           help = 'List of problems to do (default: all)')

    args = argparser.parse_args()
    with open(args.fname) as finput:
        db = Database(csvfile = finput)

    # Loop over requested problems.
    for probno in args.problems:
        if not probno in problemnos:
            raise ValueError(f'Invalid problem number: {probno}! Available problems: {problemnos}')
        # 'globals' is the dict of all variables in the current namespace.
        prob = globals()['problem' + str(probno)]
        print('*** ' + prob.__doc__)
        print()
        prob(db)
        print()
    return db

if __name__ == '__main__':
    db = main()

