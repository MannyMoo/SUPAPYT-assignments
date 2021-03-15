#!/usr/bin/env python

from Database import Database
import ROOT
from pprint import pprint
from matplotlib import pyplot as plt
from matplotlib import patches
# Use ufloat if it's available
try:
    from uncertainties import ufloat
except ImportError:
    def ufloat(val, err):
        '''Mimic ufloat but just return a regular float'''
        return float(val)

    
class LHCbDB(Database):
    '''Derived Database class to hold the LHCb data.'''

    class Distribution:
        '''The signal or background distribution of a variable.'''

        def __init__(self, label, attr, counts):
            '''Takes the label for the distribution, the binning attribute,
            and the list of counts.
            Entries in "counts" should be dicts with 'n', 'vmin', and 'vmax'
            elements.'''
            self.label = label
            self.attr = attr
            self.counts = counts

            
        def moment(self, moment = 1):
            '''Calculate the moment (mean, mean squared, etc) of the distribution.'''
            return sum(count['n'] * ((count['vmin'] + count['vmax'])/2.)**moment for count in self.counts)\
                /sum(count['n'] for count in self.counts)


        def mean(self):
            '''Get the mean of the distribution.'''
            return self.moment()


        def meansq(self):
            '''Get the mean of the square of the distribution.'''
            return self.moment(2)


        def stdev(self):
            '''Get the standard deviation of the distribution.'''
            return (self.meansq() - self.mean()**2)**.5


        def bin_values(self):
            '''Get the values at the centre of each bin.'''
            return [(count['vmin'] + count['vmax'])/2. for count in self.counts]


        def yields(self):
            '''Get the counts in each bin.'''
            try:
                # ufloat counts
                return [count['n'].nominal_value for count in self.counts]
            except AttributeError:
                # Regular float counts
                return [count['n'] for count in self.counts]

            
        def plot(self, axis = plt):
            '''Plot the distribution.'''
            axis.plot(self.bin_values(), self.yields(), label = self.label)
            plt.xlabel(LHCbDB.titles[self.attr])
            plt.ylabel('Yield')

            
    # Static methods don't require an instance of the class to be called
    @staticmethod
    def test_range(attr, vmin, vmax):
        '''Get a function to test if an entry lies in a given range.'''
        return lambda entry : vmin <= getattr(entry, attr) <= vmax


    titles = {'mass' : 'D0 mass [MeV]',
              'decaytime' : 'Decay time [ps]',
              'pt' : 'PT [MeV]',
              'ipchi2' : 'IP chi-squared'}
    

    def __init__(self, entries = [], csvfile = None, readonly = True,
                 massmin = None, massmax = None, massmean = None,
                 masswindow = None):
        '''Constructor. Takes the usual Database constructor arguments
        plus arguments to set the signal and background mass intervals.'''

        # Initialise the base Database
        super(LHCbDB, self).__init__(entries = entries, csvfile = csvfile,
                                     readonly = readonly)
        # Set the parameters for the mass ranges
        self.massmin = massmin
        self.massmax = massmax
        self.massmean = massmean
        self.masswindow = masswindow

        
    def filter(self, test):
        '''Return an LHCbDB of entries satisfying the method 'test'.'''
        db = super(LHCbDB, self).filter(test)
        return LHCbDB(entries = db.entries, massmin = self.massmin,
                      massmax = self.massmax, massmean = self.massmean,
                      masswindow = self.masswindow)

    
    def calculate_mass_ranges(self, stddevscale = 0.8):
        '''Calculate the signal and background mass ranges. The 
        background ranges will be [min, min+stddev*stddevscale]
        and [max-stddev*stddevscale, max], and the signal range
        will be [mean-stddev*stddevscale, mean+stddev*stddevscale]'''

        massstats = self.stats('mass')
        self.massmin = massstats['min']
        self.massmax = massstats['max']
        self.massmean = massstats['mean']
        self.masswindow = stddevscale * massstats['stddev']


    def in_signal_region(self, entry):
        '''Check if an entry is in the signal region.'''
        return (self.massmean - self.masswindow <= entry.mass
                <= self.massmean + self.masswindow)

    
    def in_bkg_region(self, entry):
        '''Check if an entry is in the background region.'''
        return ((self.massmin <= entry.mass <= self.massmin + self.masswindow)
                or (self.massmax - self.masswindow <= entry.mass <= self.massmax))

    
    def count_signal_background(self, selection = None):
        '''Count the number of signal and background, optionally
        applying an additional selection.'''

        # Check if the mass ranges are defined, if not, calculate them
        if None in (self.massmin, self.massmax, self.massmean, self.masswindow):
            self.calculate_mass_ranges()
        
        # Add the selection to the test functions if given
        if selection:
            def testsig(entry):
                return selection(entry) and self.in_signal_region(entry)

            def testbkg(entry):
                return selection(entry) and self.in_bkg_region(entry)
        else:
            testsig = self.in_signal_region
            testbkg = self.in_bkg_region

        # Count the number of entries passing the signal/background tests
        nsigplusbkg = self.count(testsig)
        nbkg = self.count(testbkg)
        # Convert to ufloat assuming sqrt(N) errors
        nsigplusbkg = ufloat(nsigplusbkg, nsigplusbkg**.5)
        nbkg = ufloat(nbkg, nbkg**.5)

        # Subtract the background and return n. signal and n. bkg
        return nsigplusbkg - nbkg, nbkg

    
    def plot(self, attr, label, savename, axis = plt, selection = None):
        '''Make a histogram of an attribute.'''
        histo = axis.hist(self.iterator(attr, selection = selection),
                          bins = 100, label = label)
        plt.xlabel(self.titles[attr])
        plt.ylabel('N. candidates')
        plt.savefig(savename)
        return histo

    
    def signal_significance(self, selection = None):
        '''Get n. signal, n. bkg, and the signal significance, optionally
        with a selection applied.'''
        nsig, nbkg = self.count_signal_background(selection)
        try:
            signf = nsig/(nsig + 2*nbkg)**.5
        except ZeroDivisionError:
            signf = 0.
        return nsig, nbkg, signf

    
    def optimise_cut(self, attr, vstart, vend, delta, mincut = True):
        '''Optimise a cut value for maximum signal significance.'''
        cutdb = self
        if not mincut:
            vstart, vend = vend, vstart
            delta = -delta
            cutrange = lambda cut : (float('-inf'), cut)
            test = lambda : cut > vend
        else:
            cutrange = lambda cut : (cut, float('inf'))
            test = lambda : cut < vend
        cut = vstart - delta
        cutsigs = []
        while test():
            cut += delta
            nsig, nbkg, signf = \
                self.signal_significance(LHCbDB.test_range(attr, *cutrange(cut)))
            cutsigs.append([cut, signf])
        return max(cutsigs, key = lambda val : val[1]) + [cutsigs]

    
    def signal_background_distribution(self, attr, nbins, vmin, vmax):
        '''Get the signal and background distributions of the given attribute.'''
        delta = (vmax - vmin)/nbins
        sigcounts = []
        bkgcounts = []
        while vmin < vmax:
            vmaxbin = vmin + delta
            nsig, nbkg = self.count_signal_background(LHCbDB.test_range(attr, vmin, vmaxbin))
            sigcounts.append({'n' : nsig, 'vmin' : vmin, 'vmax' : vmaxbin})
            bkgcounts.append({'n' : nbkg, 'vmin' : vmin, 'vmax' : vmaxbin})
            vmin = vmaxbin
        return LHCbDB.Distribution('Signal', attr, sigcounts), \
            LHCbDB.Distribution('Background', attr, bkgcounts)


db = LHCbDB(csvfile = 'D0KpiData.csv')

f = ROOT.TFile('MasterclassData.root')
tree = f.DecayTree

plt.yscale('log')
timehisto = db.plot('decaytime', 'All', 'D0Time-NoCuts.png')
plt.clf()
plt.yscale('linear')

massfig, massax = plt.subplots()
masshisto = db.plot('mass', 'All', 'D0Mass-NoCuts.png', massax)

massstats = db.stats('mass')
massstddev = massstats['stddev']
massmin = massstats['min'] #round(massstats['min'], 0)
massmax = massstats['max'] #round(massstats['max'], 0)
massmean = massstats['mean']
print('''1)
Find the minimum, maximum, mean and standard deviation of the values in the 
`mass` column and output these to the terminal.''')
print('mass min:', massmin, 'max:', massmax, 'mean:', massmean, 'stddev:', massstddev)
print()

massax.add_patch(patches.Rectangle((massmin, 0), massstddev*0.8, max(masshisto[0]),
                                   color = 'red', fill = False, hatch = 'X'))
massax.add_patch(patches.Rectangle((massmax - massstddev*0.8, 0), massstddev*0.8, max(masshisto[0]),
                                   color = 'red', fill = False, hatch = 'X'))
massax.add_patch(patches.Rectangle((massmean - massstddev*0.8, 0), 2*massstddev*0.8, max(masshisto[0]),
                                   color = 'blue', fill = False, hatch = 'X'))
plt.savefig('D0Mass-WBoxes.png')
plt.clf()

masshisto = db.plot('mass', 'All', 'D0Mass-NoCuts.png')

print('''2)
Similarly find and output the minimum, maximum, mean and standard deviation of 
the `decaytime` values.''')
timestats = db.print_stats('decaytime')
print('lifetime:', timestats['mean'] - timestats['min'])
print()

print('''3)
Count the number of signal and background''')
db.calculate_mass_ranges()
nsig, nbkg = db.count_signal_background()
print('N. signal:', nsig, 'n. bkg:', nbkg)
print()

print('''4)
Find the number of signal and background with ipchi2 < 13 and ipchi2 >= 13''')
ipchi2cut = 13
for ipmin, ipmax in (ipchi2cut, float('inf')), (0, ipchi2cut):
    nsig, nbkg = db.count_signal_background(LHCbDB.test_range('ipchi2', ipmin, ipmax))
    print('ipmin:', ipmin, 'ipmax:', ipmax)
    print('N. signal:', nsig, 'n. bkg:', nbkg)
print()

dboriginal = db
db = db.filter(LHCbDB.test_range('ipchi2', 0, ipchi2cut))

print('''5)
Find the optimal `pt` cut value and the signal significance that it gives''')

print('pt cut:')
ptstats = db.stats('pt')
delta = 10
ptcut = ptstats['min']
optcut, maxsig, cutsigs = db.optimise_cut('pt', ptstats['min'], 5000, 10)
# pprint(cutsigs)

dbipchi2cut = db
db = db.filter(LHCbDB.test_range('pt', optcut, float('inf')))
dbrejected = dboriginal.filter(lambda entry : entry.pt < optcut or entry.ipchi2 > ipchi2cut)

nsigcut, nbkgcut = db.count_signal_background()
print('pt cut:', optcut, 'sig sig:', maxsig, 'nsig:', nsigcut, 'nbkg:', nbkgcut)
print()

massaccepted = db.plot('mass', 'Accepted', 'D0Mass-WithCuts.png')
massrejected = dbrejected.plot('mass', 'Rejected', 'D0Mass-WithCuts.png')
plt.legend()
plt.savefig('D0Mass-WithCuts.png')

timestats = db.stats('decaytime')
tmin = round(timestats['min'], 2)
tmax = round(timestats['max'], 2)

print('''6)
Calculate the lifetime from the mean of the background subtracted decay-time distribution
as well as the standard deviation of the distribution.''')

sigdist, bkgdist = db.signal_background_distribution('decaytime', 100, tmin, tmax)
print(sigdist.mean() - timestats['min'], sigdist.stdev())

plt.clf()
sigdist.plot()
bkgdist.plot()
plt.yscale('log')
plt.legend()
plt.savefig('D0Time-wCuts-SigBkg.png')
