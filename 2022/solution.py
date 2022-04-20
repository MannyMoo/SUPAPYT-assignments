#!/usr/bin/env python3

'''Solutions to SUPAPYT assignment 2022 - analysing global per-capita C02
emissions.'''

from argparse import ArgumentParser
from Database import Database


class EmissionsDB(Database):
    '''Database for analysis of per-capita emissions.'''

    def __init__(self, entries=[], csvfile=None, readonly=True):
        '''Takes the same arguments as Database.Database.__init__:
        entries: list of Entry instances
        csvfile: file name or file object containing data in csv format
        readonly: whether the DB should be read only'''
        # Initialise the base class
        super(EmissionsDB, self).__init__(entries=entries,
                                          csvfile=csvfile,
                                          readonly=readonly)

        # Check that the DB has the expected columns
        expected = ('Country Name', 'Region', 'IncomeGroup')
        columns = list(self.Entry.attributes())
        # First the non-year columns
        for column in expected:
            try:
                columns.remove(column)
            except ValueError:
                raise ValueError(f'Expected column {column!r} is missing!')
        # All remaining columns should be years
        for column in columns:
            if not column.isnumeric():
                raise ValueError(('Expected only year columns in addition'
                                  ' to {expected}, but found a column'
                                  ' {column!r}').format(expected=expected,
                                                        column=column))
        # Tuple of years
        self.years = tuple(columns)

    # We don't need to access the DB in this function, but logically
    # it belongs to the DB class, so make it a static method
    @staticmethod
    def sum_emissions(entry, years):
        '''Sum the emissions of the entry over the given years.'''
        return sum(entry[i] for i in years if entry[i] != '')

    def summed_emissions(self, years=None):
        '''Get the total emissions of all countries over the given years
        (default all years). Returns a dict {country : sum}.'''
        if years is None:
            years = self.years
        # Call the static method on the class rather than self to make
        # it clear that it's a static method being called
        return {entry['Country Name'] : EmissionsDB.sum_emissions(entry, years)
                for entry in self}

    def get_grouped_DB(self, group):
        '''Make a DB of countries grouped by the column 'group' 
        (eg, Region).'''
        # For each value of the group column, make a dict with the expected
        # column values. 'Country Name' is swapped for the group, 'Region'
        # and 'IncomeGroup' are set to null. Initialise the emissions
        # for each year to zero.
        groups = {}
        for gr in set(self.iterator(group)):
            initvals = {'Country Name' : gr,
                        'Region' : '',
                        'IncomeGroup' : ''}
            for year in self.years:
                initvals[year] = 0.
            groups[gr] = initvals

        for entry in self:
            # Get the group for this entry
            entryGroup = groups[entry[group]]
            # Loop over years and add non-null values to the emissions
            # for the group.
            for year in self.years:
                if entry[year] == '':
                    continue
                entryGroup[year] += entry[year]

        # Make Database.Entry instances for each group
        grEntries = [self.Entry(**vals) for vals in groups.values()]
        # Make a DB of the entries
        grDB = EmissionsDB(grEntries)
        return grDB

    def sum_and_sort_emissions(self, years=None, output=True):
        '''Sum emissions over the given years for the entries in the database,
        then sort by total emissions.'''
        if years is None:
            years = self.years
        # Get total emissions for each country for the given years
        sums = {entry['Country Name'] : EmissionsDB.sum_emissions(entry, years)
                for entry in self}
        # Sort by the total emissions to get a list of pairs of (country, sum)
        sums = sorted(sums.items(), key=lambda x : x[1],
                      reverse=True)
        # Print if requested
        if output:
            for name, tot in sums:
                print('{0:<30}: {1:8.2f} tpc'.format(name, tot))
        return sums

    def sum_and_sort_per_decade(self, output=True):
        '''Sum emissions for each entry and sort by total emissions,
        for each decade.'''
        # Take the first 3 digits of the years to get the decades
        # eg, 1967 -> 196.
        decades = sorted(set(year[:-1] for year in self.years))
        decadeSums = {}
        for decade in decades:
            # The years for each decade are all those starting with
            # the same 3 digits.
            decadeYears = list(filter(lambda year : year.startswith(decade),
                                      self.years))
            if output:
                print('--- Decade:', decade + '0')
            # Sum and sort for each decade, and print the results
            sums = self.sum_and_sort_emissions(decadeYears, output)
            decadeSums[decade + '0'] = sums
        return decadeSums


def prob1(db):
    '''Find the countries with the lowest and highest emissions in 1960,
    and similarly in 2018 (ignoring countries with no data for the given year).
    Print the names of the countries and their emissions for each year.'''
    for year in '1960', '2018':
        minCountry = db.min_entry(year)
        maxCountry = db.max_entry(year)
        print('Year:', year)
        print('Min. emissions: {name:<18} - {emissions:7.3f} tpc'
              .format(name=minCountry['Country Name'],
                      emissions=minCountry[year]))
        print('Max. emissions: {name:<18} - {emissions:7.3f} tpc'
              .format(name=maxCountry['Country Name'],
                      emissions=maxCountry[year]))

        print()


def prob2(db):
    '''Find the and print mean and standard deviation of the emissions across
    all countries in 1960 & 2018 (ignoring countries that have no data for
    the given year).'''
    for year in '1960', '2018':
        print('Stats for', year, ' [tpc]:')
        db.print_stats(year, '7.3f')
        print()


def prob3(db):
    '''Find the countries with the lowest and highest total emissions
    summed over all years for which there's data. Print their names and
    total emissions.'''
    # Sum the emissions over years for each country
    sums = db.summed_emissions()
    # Find the min & max
    mincountry = min(sums.items(), key=lambda entry : entry[1])
    maxcountry = max(sums.items(), key=lambda entry : entry[1])
    print('Min. total emissions: {0:<18} - {1:7.2f} tpc'.format(*mincountry))
    print('Max. total emissions: {0:<18} - {1:7.2f} tpc'.format(*maxcountry))


def grouped_DBs(db, *groups):
    '''Make DBs grouped by the given column names.'''
    dbs = {}
    for group in groups:
        grdb = db.get_grouped_DB(group)
        dbs[group] = grdb
    return dbs


def prob4(grDBs):
    '''Sum the total emissions for all countries in each region across all years.
    Print a list of the regions and their total emissions, ordered by their 
    emissions. Do the same grouping the countries by income group.'''
    # Get the years from the first DB
    for group, grDB in grDBs.items():
        print('Grouped by', group, ':')
        grDB.sum_and_sort_emissions()
        print()


def prob5(grDBs):
    '''Similarly to problem 4, group the countries by region, then, for each
    decade in the range 1960s-2010s, calculate the total emissions of each
    region in that decade, then print the regions and their total emissions
    sorted by emissions. Do the same grouping the countries by income group.'''
    for group, db in grDBs.items():
        print('Group by', group)
        db.sum_and_sort_per_decade()
        print()


def main(inputfile, *problems):
    '''Solve the assignment problems.'''
    db = EmissionsDB(csvfile=inputfile)
    grDBs = None
    if '4' in problems or '5' in problems:
        grDBs = grouped_DBs(db, 'Region', 'IncomeGroup')
    funcs = {'1' : (prob1, db),
             '2' : (prob2, db),
             '3' : (prob3, db),
             '4' : (prob4, grDBs),
             '5' : (prob5, grDBs)}
    for prob in sorted(problems):
        func, arg = funcs[prob]
        print('*** Problem', prob)
        print('   ', func.__doc__)
        func(arg)
        print()


if __name__ == '__main__':
    parser = ArgumentParser('solution.py',
                            description='SUPAPYT 2022 assignment problems'
                            ' - analyse global per-capita CO2 emissions')
    
    parser.add_argument('--inputfile', default='PerCapitaC02Emissions.csv',
                        help='Name of the csv file containing the data.')
    problems = list(map(str, range(1, 6)))
    parser.add_argument('--problems', nargs='*', default=problems,
                        choices=problems,
                        help='Which problems to solve')

    args = parser.parse_args()
    main(args.inputfile, *args.problems)
                        
