#!/usr/bin/env python3

'''Solutions to SUPAPYT assignment 2022.'''

from Database import Database


def prob1(db):
    '''Find the countries with the lowest and highest emissions in 1960,
    and similarly in 2018 (ignoring countries with no data for the given year).
    Print the names of the countries and their emissions for each year.'''
    for year in '1960', '2018':
        mincountry = db.min_entry(year)
        maxcountry = db.max_entry(year)
        print('Year:', year, 'min. emissions:', mincountry['Country Name'],
              round(mincountry[year], 3), 'max. emissions:',
              maxcountry['Country Name'], round(maxcountry[year], 3))
    

def prob2(db):
    '''Find the and print mean and standard deviation of the emissions across all
    countries in 1960 & 2018 (ignoring countries that have no data for the given year).'''
    for year in '1960', '2018':
        print(year)
        db.print_stats(year)


def get_years(db):
    '''Get a tuple of year columns in the DB.'''
    return tuple(column for column in db.Entry.attributes() if column.isnumeric())


def sum_emissions(entry, years):
    '''Sum the emissions of the entry over the given years.'''
    return sum(entry[str(i)] for i in years
               if entry[str(i)] != '')

def prob3(db):
    '''Find the countries with the lowest and highest total emissions
    summed over all years for which there's data. Print their names and
    total emissions.'''
    # Sum the emissions over years for each country
    years = get_years(db)
    sums = {entry['Country Name'] : sum_emissions(entry, years)
            for entry in db}
    # Find the min & max
    mincountry = min(sums.items(), key=lambda entry : entry[1])
    maxcountry = max(sums.items(), key=lambda entry : entry[1])
    print('Min. total emissions: {0} {1:.2f}'.format(*mincountry))
    print('Max. total emissions: {0} {1:.2f}'.format(*maxcountry))


def make_grouped_DB(db, group):
    '''Group entries by their values of 'group' and sum together their emissions.'''
    groups = {}
    years = get_years(db)
    for gr in set(db.iterator(group)):
        initvals = {'Country Name' : gr,
                    'Region' : '',
                    'IncomeGroup' : ''}
        for year in years:
            initvals[year] = 0.
        groups[gr] = initvals
    for entry in db:
        for year in years:
            if entry[year] == '':
                continue
            groups[entry[group]][year] += entry[year]
    grentries = [db.Entry(**vals) for vals in groups.values()]
    grdb = Database(grentries)
    return grdb


def sum_and_sort_emissions(db, years, output=True):
    '''Sum emissions over the given years for the entries in the database,
    then sort by total emissions.'''
    sums = {entry['Country Name'] : sum_emissions(entry, years)
            for entry in db}
    if output:
        for name, tot in sorted(sums.items(), key=lambda x : x[1],
                                reverse=True):
            print('{0:<30}: {1:.2f}'.format(name, tot))
    return sums
    
def prob4(db):
    '''Sum the total emissions for all countries in each region across all years.
    Print a list of the regions and their total emissions, ordered by their emissions.
    Do the same grouping the countries by income group.'''
    dbs = {}
    years = get_years(db)
    
    for group in 'Region', 'IncomeGroup':
        grdb = make_grouped_DB(db, group)
        print('Grouped by', group, ':')
        sum_and_sort_emissions(grdb, years)
        dbs[group] = grdb
        print()
    return dbs


def prob5(grdbs):
    '''Similarly to problem 4, group the countries by region, then, for each
    decade in the range 1960s-2010s, calculate the total emissions of each
    region in that decade, then print the regions and their total emissions
    sorted by emissions. Do the same grouping the countries by income group.'''
    for group, db in grdbs.items():
        print('Group by', group)
        years = get_years(db)
        decades = sorted(set(year[:-1] for year in years))
        for decade in decades:
            decadeyears = list(filter(lambda year : year.startswith(decade),
                                      years))
            print('Decade:', decade + '0')
            sum_and_sort_emissions(db, decadeyears)
        print()
            
if __name__ == '__main__':
    db = Database(csvfile='PerCapitaC02Emissions.csv')
    prob1(db)
    prob2(db)
    prob3(db)
    grdbs = prob4(db)
    prob5(grdbs)
