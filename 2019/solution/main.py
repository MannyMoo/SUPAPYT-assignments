#!/usr/bin/env python3

from Database import Database
from datetime import datetime
from collections import Counter

def try_int(val) :
    '''Try to convert something to an int. Return 0 on failure.'''
    try :
        return int(val)
    except :
        return 0

def round_down(val, div = 10) :
    '''Round down to the nearest 'div'.'''
    return (val//div) * 10
    
class SUPAPYTProblems :
    '''Solve 2019 SUPAPYT problem set.'''
    
    def __init__(self, fname) :
        '''Constructor. Takes the name of the data file to analyse.'''

        self.db = Database()
        with open(fname) as finput :
            self.db.read_from_csv((line for line in finput if not line.startswith('#')),
                                  True, delimiter = '\t')

    def get_date(self, entry) :
        '''Get the date as a datetime instance from a DB entry.'''

        if not entry.Year :
            return ''
        return datetime(year = try_int(entry.Year),
                        month = max(try_int(entry.Mo), 1),
                        day = max(try_int(entry.Da), 1),
                        hour = try_int(entry.Ho),
                        minute = try_int(entry.Mi),
                        second = try_int(entry.Se))

    def print_info(self, entry) :
        '''Print Magnitude, Area, Lat & Lon, and Date for a DB entry.'''

        for attr, width in ('M', 5), ('Area', 25), ('Lat', 6), ('Lon', 6) :
            print(attr + ':', str(getattr(entry, attr)).rjust(width), end = ', ')
        print('Date:', self.get_date(entry))

    def print_prob(self, n) :
        '''Print the number of the problem surrounded by '*'.'''

        print('*' * 10, 'Prob', n, '*' * 10)

    def problem_1(self) :
        '''Find the smallest and largest magnitudes of any earthquakes in the file
        (the "M" field). Find all earthquakes with these magnitudes (there's more 
        than one for each) and print their magnitudes, location ("Area"), latitude 
        and longitude ("Lat" & "Lon"), and their date ("Year", "Mo", "Da", "Ho", 
        "Mi" & "Se").'''

        # Get the min & max values.
        magmin = self.db.min('M')
        magmax = self.db.max('M')

        # Get the entries with those values & print their info.
        print('Smallest:')
        for entry in self.db.filter_matching('M', magmin) :
            self.print_info(entry)
        print()
        print('Largest:')
        for entry in self.db.filter_matching('M', magmax) :
            self.print_info(entry)
        print()

    def problem_2(self) :
        '''Find the earliest and latest entries in the file (using "Year", "Mo", "Da", 
        "Ho", "Mi" & "Se" and the datetime class from the datetime module). Print the
        same information about them as in problem 1. If the "Mo" or "Da" attributes 
        are missing for an entry, their value should be taken as 1. If the "Ho", "Mi"
        or "Se" attributes are missing, they should be taken as 0.'''

        # Get the earliest & latest entries.
        datemin = self.db.min(self.get_date)
        datemax = self.db.max(self.get_date)

        # Print the info on entries with those dates.
        print('Earliest:')
        for entry in self.db.filter_matching(self.get_date, datemin) :
            self.print_info(entry)
        print('Latest:')
        for entry in self.db.filter_matching(self.get_date, datemax) :
            self.print_info(entry)
        print()

    def problem_3(self) :
        '''Find the mean, median, and standard deviation of the magnitudes ("M"). Do the
        same for the depths ("Dep"), ignoring any entries that are missing a depth 
        measurement.'''

        # Just use the stats methods in the Database class.
        print('Magnitude:')
        self.db.print_stats('M', form = '5.2f')
        print()
        print('Depth [km]:')
        self.db.print_stats('Dep', form = '5.2f')
        print()

    def problem_4(self) :
        '''Print the number of earthquakes that were recorded in each decade (eg, 1000-1009
        inclusive) between 1000 and 1909.'''

        # Find the earliest & latest years.
        earliest = self.db.min('Year')
        latest = self.db.max('Year')

        # Use Counter class to count how many entries belong to each decade.
        decadecount = Counter(round_down(entry.Year) for entry in self.db)

        # Loop over the decades and print the number in each.
        print('Number of earthquakes per decade:')
        for decade in range(int(round_down(earliest)), int(round_down(latest)) + 10, 10) :
            print(decade, decadecount.get(decade, 0))

        print()

    def problem_5(self) :
        '''Divide longitude ("Lon") in 10 degree intervals from -180 to +180 (eg, 
        -180 <= Lon < -170, -170 <= Lon < -160, etc) and print the number of earthquakes 
        recorded in each interval, ignoring any entries that don't have a longitude value
        (empty string). What's the most active interval?'''

        # Again use Counter to count the number of entries in each Lon interval.
        areacount = Counter(round_down(lon) for lon in self.db.iterator('Lon'))

        # Loop over Lon intervals and print the number in each.
        print('Number of earthquakes per 10 Deg. interval in longitude:')
        for lon in range(-180, 180, 10) :
            print('{0:4d} to {1:4d} Deg.: {2}'.format(lon, lon+10, areacount.get(lon, 0)))

        # Find the maximum interval and its count using 'items' to get the 
        maxarea, maxcount = max(areacount.items(), key = lambda v : v[1])
        print('Most active region:', maxarea, 'to', maxarea + 10, 'Deg. :', maxcount)

    def do_problems(self, *problems) :
        '''Do the problems with the given numbers (as ints).'''
        
        for i in problems :
            try :
                func = getattr(self, 'problem_' + str(i))
            except AttributeError :
                raise ValueError('Invalid problem number: ' + str(i)
                                 + '\nValid numbers are: ' + str(self.problem_numbers()))
            self.print_prob(i)
            if func.__doc__ :
                print(func.__doc__.replace(' ' * 8, ''))
                print()
            func()

    def problem_numbers(self) :
        '''Get the problem numbers.'''

        return list(range(1, 6))
    
    def do_all_problems(self) :
        '''Do all the problems.'''
        
        self.do_problems(*self.problem_numbers())
        
def main() :
    '''Parse commandline arguments for the input file name and problems to do,
    then do the problems.'''
    
    from argparse import ArgumentParser

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
    argparser.add_argument('--problems', nargs = '*', default = [],
                           help = 'List of problems to do (default: all)')

    args = argparser.parse_args()

    probs = SUPAPYTProblems(args.fname)
    if not args.problems :
        probs.do_all_problems()
    else :
        probs.do_problems(*args.problems)

if __name__ == '__main__' :
    main()
