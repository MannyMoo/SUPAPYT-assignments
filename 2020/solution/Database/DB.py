'''Generic database class for statistical analysis.'''

from Database.Entry import class_factory
from csv import DictReader, DictWriter
import statistics

class Database(object) :
    '''Generic database class for statistical analysis.'''

    # Just contains the list of entries, and the class type of the entries.
    __slots__ = ('entries', 'Entry')

    class DBIterator(object) :
        '''Iterator over an attribute of the entries in the database.'''
        __slots__ = ('db', 'getter')
        
        def __init__(self, db, attr) :
            '''Constructor, takes the Database and the name of the attribute 
            over which to iterate.'''
            
            self.db = db
            if isinstance(attr, str) :
                self.getter = lambda entry : getattr(entry, attr)
            else :
                self.getter = attr

            # Just to check that the db Entry class has the given attr,
            # will raise an exception if not.
            if self.db.entries :
                self.getter(self.db.entries[0])


        def __iter__(self) :
            '''Iterate over the entries.'''
            return (self.getter(entry) for entry in self.db.entries)

        def __len__(self) :
            '''Get the number of elements in the sequence.'''

            return len(self.db.entries)
        
    class DBNonNullIterator(DBIterator) :
        '''Iterator over entries in the Database with non-null values of 
        a given attribute.'''

        __slots__ = ('null',)
        
        def __init__(self, db, attr, null = '') :
            '''Constructor, takes the Database and the name of the attribute 
            over which to iterate.'''
            super().__init__(db, attr)
            self.null = null
            
        def __iter__(self) :
            '''Iterate over the entries with non-null values.'''
            return (self.getter(entry) for entry in self.db.entries \
                    if self.getter(entry) != self.null)

        def __len__(self) :
            '''Get the number of elements in the sequence.'''
            # This is required to use functions from the statistics module.
            # It's a little sub-optimal as it requires looping over all
            # the elements to get the number that're non-null, but still
            # preferable to reimplementing the stats functions.
            # 'n' could be cached, but then we'd have to check every time
            # if the DB has changed at all, which would probably be slower.
            n = 0
            for i in self :
                n += 1
            return n
        
    def __init__(self, entries = [], csvfile = None, readonly = True) :
        '''Constructor. Can take the list of entries and/or an open file in csv 
        format from which to read the entries. readonly defines whether the
        entries can be modified.'''
        self.entries = list(entries)
        # Keep a reference to the class of the entries in the list.
        if self.entries :
            self.Entry = self.entries[0].__class__
        else :
            self.Entry = None
        if csvfile:
            self.read_from_csv(csvfile, readonly)
            
    def read_from_csv(self, datafile, readonly, attrs = None, **kwargs) :
        '''Read from an open file (or other iterable) using csv.DictReader. 
        If attrs is given it defines the names of the columns in the file; 
        if not given the names are taken from the first line in the file.'''

        if not attrs :
            reader = DictReader(datafile, **kwargs)
        else :
            reader = DictReader(datafile, fieldnames = attrs, **kwargs)

        self.Entry = class_factory(readonly, *reader.fieldnames)
        for row in reader :
            self.entries.append(self.Entry(**row))

    def write_to_csv(self, fname) :
        '''Write the db to a file in csv format.'''

        # Needs to be opened in binary mode (on Windows)
        with open(fname, 'w') as foutput :
            attrs = self.Entry.attributes()
            writer = DictWriter(foutput, attrs)
            writer.writeheader()
            for entry in self :
                writer.writerow({attr : getattr(entry, attr) for attr in attrs})
            
    def iterator(self, attr) :
        '''Get an iterator over an attribute of the entries in the db.'''
        return Database.DBIterator(self, attr)

    def non_null_iterator(self, attr, null = '') :
        '''Get an iterator over an attribute of the entries in the db 
        for entries with non-null values.'''
        return Database.DBNonNullIterator(self, attr, null)
    
    def _stat(self, attr, operation, default = None, null = '') :
        '''Calculate a statistic on the attribute 'attr' using the method
        'operation' on non-null entries in the db. If there're no non-null
        entries, return 'default'.'''
        # Check that there's at least one non-null value in the db.
        if any(True for val in self.non_null_iterator(attr, null)) :
            return operation(self, attr, null)
        return default

    def mean(self, attr, null = '') :
        '''Calculate the mean of non-null entries. Returns None if there're
        no non-null entries.'''
        return self._stat(attr,
                          (lambda self, attr, null : statistics.mean(self.non_null_iterator(attr, null))),
                          null)

    def _meansq(self, attr, null) :
        '''Calculate the mean of the square of non-null entries.'''
        n = 0
        meansq = 0.
        for val in self.non_null_iterator(attr, null) :
            meansq += val**2.
            n += 1
        return meansq/n
        
    def meansq(self, attr, null = '') :
        '''Calculate the mean of the square of non-null entries. Returns None
        if there're no non-null entries.'''
        return self._stat(attr, Database._meansq, null)

    def stddev(self, attr, null = '') :
        '''Calculate the standard deviation of non-null entries. Returns None
        if there're no non-null entries.'''
        try:
            return self._stat(attr,
                              (lambda self, attr, null : \
                               statistics.stdev(self.non_null_iterator(attr, null))),
                              null)
        # In case there's only one non-null entry
        except statistics.StatisticsError:
            return 0.
        
    def min(self, attr, null = '') :
        '''Get the minimum of non-null entries. Returns None if there're no 
        non-null entries.'''
        return self._stat(attr,
                          (lambda self, attr, null : min(self.non_null_iterator(attr, null))),
                          null)

    def max(self, attr, null = '') :
        '''Get the maximum of non-null entries. Returns None if there're no 
        non-null entries.'''
        return self._stat(attr,
                          (lambda self, attr, null : max(self.non_null_iterator(attr, null))),
                          null)

    def median(self, attr, null = '') :
        '''Get the median of non-null entries. Returns None if there're no 
        non-null entries.'''
        return self._stat(attr,
                          (lambda self, attr, null : statistics.median(self.non_null_iterator(attr, null))),
                          null)

    def stats(self, attr, null = '') :
        '''Get a dict of the min, max, mean, median and standard deviation of
        non-null entries.'''
        return {'min' : self.min(attr, null),
                'max' : self.max(attr, null),
                'mean' : self.mean(attr, null),
                'median' : self.median(attr, null),
                'stddev' : self.stddev(attr, null),
                'n' : self.n_non_null(attr, null)}

    def print_stats(self, attr, form = None) :
        '''Print the min, max, mean, median and standard deviation of non-null 
        entries. Optionally provide a formatting string, eg '4.2f'.'''
        if form :
            form = '{0:' + form + '}'
        else :
            form = '{0}'
        stats = self.stats(attr)
        for attr in 'n', 'min', 'max', 'mean', 'median', 'stddev' :
            print(attr.ljust(6), ':', form.format(stats[attr]))
            
    def sort(self, attr) :
        '''Sort the entries according to the value of the given attribute.'''
        if isinstance(attr, str) :
            getter = lambda entry : getattr(entry, attr)
        else :
            getter = attr
        self.entries.sort(key = getter)

    def filter(self, test) :
        '''Return a Database of entries satisfying the method 'test'.'''
        return Database(filter(test, self.entries))

    def filter_matching(self, attr, val) :
        '''Filter entries where attr == val.'''
        iterator = self.iterator(attr)
        return self.filter(lambda entry : iterator.getter(entry) == val)

    def min_entry(self, attr, null = ''):
        '''Get the entry with the minimum value of the given attribute.'''
        return min((entry for entry in self if getattr(entry, attr) != null),
                   key = lambda entry : getattr(entry, attr))

    def max_entry(self, attr, null = ''):
        '''Get the entry with the minimum value of the given attribute.'''
        return max((entry for entry in self if getattr(entry, attr) != null),
                   key = lambda entry : getattr(entry, attr))

    def __iter__(self) :
        '''Iterate over entries in the db.'''
        return iter(self.entries)

    def __len__(self) :
        '''Get the number of entries in the db.'''
        return len(self.entries)

    def __getitem__(self, i) :
        '''Get an entry by index.'''
        return self.entries[i]

    def __bool__(self):
        '''Returns True if there're entries in the DB, else False.'''
        return bool(self.entries)
    
    def n_non_null(self, attr, null = ''):
        '''Get the number of entries that have a non-null value for the given
        attribute.'''
        return len(self.non_null_iterator(attr, null))
