#!/usr/bin/env python

'''Assignment solution for SUPAPYT 2021 - finding the lifetime of the D0 meson
from LHCb data.'''

from Database import Database
from matplotlib import pyplot as plt
from matplotlib import patches
from argparse import ArgumentParser
# Use ufloat if it's available
try:
    raise ImportError
    from uncertainties import ufloat
except ImportError:
    def ufloat(val, err):
        '''Mimic ufloat constructor but just return a regular float'''
        return float(val)


class LHCbDB(Database):
    '''Derived Database class to hold the LHCb data.'''

    class Distribution:
        '''The signal or background distribution of a variable.'''

        def __init__(self, label, attr, counts, xlabel = None, ylabel = 'Yield'):
            '''Takes the label for the distribution, the binning attribute,
            the list of counts, and optionally x and y axis labels.
            Entries in "counts" should be dicts with 'n', 'vmin', and 'vmax'
            elements.'''
            self.label = label
            self.attr = attr
            self.counts = counts
            if xlabel:
                self.xlabel = xlabel
            else:
                self.xlabel = LHCbDB.titles[self.attr]
            self.ylabel = ylabel
            
        def moment(self, moment=1):
            '''Calculate the moment (mean, mean squared, etc) of the distribution.'''
            return sum(count['n'] * ((count['vmin'] + count['vmax'])/2.)**moment for count in self.counts)\
                / sum(count['n'] for count in self.counts)

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

        def plot(self, axis=plt):
            '''Plot the distribution.'''
            axis.plot(self.bin_values(), self.yields(), label=self.label)
            plt.xlabel(self.xlabel)
            plt.ylabel(self.ylabel)

    # Static methods don't require an instance of the class to be called
    @staticmethod
    def test_range(attr, vmin, vmax):
        '''Get a function to test if an entry lies in a given range.'''
        return lambda entry: vmin <= getattr(entry, attr) < vmax

    # The axis titles for each variable
    titles = {'mass': 'D0 mass [MeV]',
              'decaytime': 'Decay time [ps]',
              'pt': 'PT [MeV]',
              'ipchi2': 'IP chi-squared'}

    def __init__(self, entries=[], csvfile=None, readonly=True,
                 massmin=None, massmax=None, massmean=None,
                 masswindow=None):
        '''Constructor. Takes the usual Database constructor arguments
        plus arguments to set the signal and background mass intervals.'''

        # Initialise the base Database
        super(LHCbDB, self).__init__(entries=entries, csvfile=csvfile,
                                     readonly=readonly)
        # Set the parameters for the mass ranges
        self.massmin = massmin
        self.massmax = massmax
        self.massmean = massmean
        self.masswindow = masswindow

    def filter(self, test):
        '''Return an LHCbDB of entries satisfying the method 'test'.'''
        # Use Database.filter from the base class 
        db = super(LHCbDB, self).filter(test)
        # Copy the mass window info from this LHCbDB
        return LHCbDB(entries=db.entries, massmin=self.massmin,
                      massmax=self.massmax, massmean=self.massmean,
                      masswindow=self.masswindow)

    def calculate_mass_ranges(self, stddevscale=0.8):
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

    def count_signal_background(self, selection=None):
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

    def plot(self, attr, label, savename = None, axis=plt, selection=None):
        '''Make a histogram of an attribute.'''
        histo = axis.hist(self.iterator(attr, selection=selection),
                          bins=100, label=label)
        plt.xlabel(self.titles[attr])
        plt.ylabel('N. candidates')
        if savename:
            plt.savefig(savename)
        return histo

    def signal_significance(self, selection=None):
        '''Get n. signal, n. bkg, and the signal significance, optionally
        with a selection applied.'''
        nsig, nbkg = self.count_signal_background(selection)
        try:
            signf = nsig/(nsig + 2*nbkg)**.5
        except ZeroDivisionError:
            signf = 0.
        return nsig, nbkg, signf

    def optimise_cut(self, attr, vstart, vend, delta, mincut=True):
        '''Optimise a cut value for maximum signal significance.'''
        # attr < cut
        if not mincut:
            # Start at the maximum range and decrease in increments
            vstart, vend = vend, vstart
            delta = -delta
            # Get the accepted interval
            def cutrange(cut): return (float('-inf'), cut)
            # Check if the cut value is in range
            def test(): return cut >= vend
        # attr > cut
        else:
            def cutrange(cut): return (cut, float('inf'))
            def test(): return cut <= vend
        cut = vstart
        cutsigs = []
        # Increment the cut value until it exceeds the given range
        while test():
            # Evaluate the signal significance given the cut
            nsig, nbkg, signf = \
                self.signal_significance(
                    LHCbDB.test_range(attr, *cutrange(cut)))
            # Store the cut value and the significance
            cutsigs.append({'vmin' : cut, 'vmax' : cut, 'n' : signf})
            # Increment the cut value
            cut += delta
        # Make the distribution of signal significance vs cut value
        xlabel = LHCbDB.titles[attr] + (' >= ' if mincut else ' < ') + ' cut value'
        distr = LHCbDB.Distribution('Signal significance', attr, cutsigs,
                                    xlabel = xlabel, ylabel = 'Signal significance')
        # Return the cut value that gives the maximum significance,
        # the maximum significance, and the Distribution of significance
        # vs cut value
        maxsig = max(cutsigs, key=lambda val: val['n'])
        return maxsig['vmin'], maxsig['n'], distr

    def signal_background_distribution(self, attr, nbins, vmin, vmax):
        '''Get the signal and background distributions of the given attribute.'''
        # Bin width
        delta = (vmax - vmin)/nbins
        sigcounts = []
        bkgcounts = []
        # Loop over intervals in increments of the bin width and count
        # the signal and background in each. Store the counts and
        # the interval values in a list.
        while vmin < vmax:
            vmaxbin = vmin + delta
            nsig, nbkg = self.count_signal_background(
                LHCbDB.test_range(attr, vmin, vmaxbin))
            sigcounts.append({'n': nsig, 'vmin': vmin, 'vmax': vmaxbin})
            bkgcounts.append({'n': nbkg, 'vmin': vmin, 'vmax': vmaxbin})
            vmin = vmaxbin
        # Return the Distributions of signal and background
        return LHCbDB.Distribution('Signal', attr, sigcounts), \
            LHCbDB.Distribution('Background', attr, bkgcounts)


def prob1(db):
    '''1)
    Find the minimum, maximum, mean and standard deviation of the values in the 
    `mass` column and output these to the terminal.'''

    print('Statistics of mass [MeV]:')
    massstats = db.print_stats('mass', form='.2f')
    return massstats


def plot_mass_and_time(db, massstats):
    '''Plot the mass and decaytime distributions.'''
    massstddev = massstats['stddev']
    massmin = massstats['min']
    massmax = massstats['max']
    massmean = massstats['mean']

    # Plot the mass
    massfig, massax = plt.subplots()
    masshisto = db.plot('mass', 'All', 'D0Mass-NoCuts.png', massax)

    # Add hatched areas to show the signal and background regions
    massax.add_patch(patches.Rectangle((massmin, 0), massstddev*0.8,
                                       max(masshisto[0]), color='red',
                                       fill=False, hatch='X'))
    massax.add_patch(patches.Rectangle((massmax - massstddev*0.8, 0),
                                       massstddev*0.8, max(masshisto[0]),
                                       color='red', fill=False, hatch='X'))
    massax.add_patch(patches.Rectangle((massmean - massstddev*0.8, 0),
                                       2*massstddev*0.8, max(masshisto[0]),
                                       color='blue', fill=False, hatch='X'))
    plt.savefig('D0Mass-WBoxes.png')
    plt.clf()

    # Plot the decaytime
    plt.yscale('log')
    db.plot('decaytime', 'All', 'D0Time-NoCuts.png')
    plt.clf()
    plt.yscale('linear')

    
def prob2(db):
    '''2)
    Similarly find and output the minimum, maximum, mean and standard deviation of 
    the `decaytime` values.'''

    print('Statistics of decaytime [ps]:')
    timestats = db.print_stats('decaytime', form='.4f')
    print('lifetime: {:.4f}'.format(timestats['mean'] - timestats['min']))
    return timestats


def prob3(db):
    '''3)
    Count the number of signal and background'''
    # This would be done automatically the first time
    # count_signal_background is called, but do it explicitly
    # just to be clear
    db.calculate_mass_ranges()
    nsig, nbkg = db.count_signal_background()
    print('N. signal:', nsig)
    print('N. bkg   :', nbkg)
    return nsig, nbkg


def prob4(db, ipchi2cut):
    '''4)
    Find the number of signal and background with ipchi2 < 13 and ipchi2 >= 13'''
    # Loop over the two cut ranges [cut, +inf) and [0, cut) and count
    # the signal and background in each.
    # Note that you can use float('inf') for infinity
    for name, ipmin, ipmax in [('ipchi2 >= ' + str(ipchi2cut), ipchi2cut, float('inf')),
                               ('ipchi2 < ' + str(ipchi2cut), 0, ipchi2cut)]:
        nsig, nbkg = db.count_signal_background(
            LHCbDB.test_range('ipchi2', ipmin, ipmax))
        print(name)
        print('N. signal:', nsig)
        print('N. bkg   :', nbkg)
    # Filter with the < cut.
    return db.filter(LHCbDB.test_range('ipchi2', 0, ipchi2cut))


def prob5(db):
    '''5)
    Find the optimal `pt` cut value and the signal significance that it gives'''

    # Increment from the minimum PT up to 5000 in steps of 10
    ptmin = db.min('pt')
    ptmax = 5000
    delta = 10
    # Get the optimal cut value
    optcut, maxsig, sigdistr = db.optimise_cut('pt', ptmin, ptmax, delta)
    # Filter with the optimal cut
    db = db.filter(LHCbDB.test_range('pt', optcut, float('inf')))
    # Count the signal and background
    nsigcut, nbkgcut = db.count_signal_background()
    print(f'''Optimal pt cut: {optcut:.2f}
N. signal: {nsigcut}
N. bkg   : {nbkgcut}
Signal significance: {maxsig:.2f}''')

    # Save the plot of significance vs PT cut
    sigdistr.plot()
    plt.savefig('SigSignificance-vs-PTCut.png')
    plt.clf()
    
    return db, optcut


def plot_mass_after_selection(db, dboriginal, optcut, ipchi2cut):
    '''Plot the mass before and after the candidate selection with the
    optimal pt cut and ipchi2 cut.'''
    # Database of rejected candidates
    dbrejected = dboriginal.filter(
        lambda entry: entry.pt < optcut or entry.ipchi2 > ipchi2cut)
    # Overlay the plots for all, accepted & rejected candidates
    dboriginal.plot('mass', 'All')
    db.plot('mass', 'Accepted')
    dbrejected.plot('mass', 'Rejected')
    plt.legend()
    plt.savefig('D0Mass-WithCuts.png')


def prob6(db):
    '''6)
    Calculate the lifetime from the mean of the background subtracted
    decay-time distribution as well as the standard deviation of the 
    distribution.'''

    # Get the decay-time range
    tmin = round(db.min('decaytime'), 2)
    tmax = round(db.max('decaytime'), 2)

    # Get the signal and background distributions
    sigdist, bkgdist = db.signal_background_distribution(
        'decaytime', 100, tmin, tmax)
    # Calculate the lifetime from the mean and stdev.
    print('''Lifetime from mean : {0:.4f} ps
Lifetime from stdev: {1:.4f} ps'''.format(sigdist.mean() - tmin,
                                          sigdist.stdev()))

    return sigdist, bkgdist


def plot_signal_background_time(sigdist, bkgdist):
    '''Plot the signal and background decay-time distributions.'''
    plt.clf()
    sigdist.plot()
    bkgdist.plot()
    plt.yscale('log')
    plt.legend()
    plt.savefig('D0Time-wCuts-SigBkg.png')


def main():
    '''Solve all the problems.'''

    # Simple use of ArgumentParser to have an optional argument to
    # the script that defines the input file name.
    parser = ArgumentParser()
    parser.add_argument('fname', nargs='?', default='D0KpiData.csv')

    # Parse the commandline arguments
    args = parser.parse_args()

    # Make the DB
    db = LHCbDB(csvfile=args.fname)

    # Solve all the problems and make some nice plots
    print(prob1.__doc__)
    print()
    massstats = prob1(db)
    print()
    plot_mass_and_time(db, massstats)
    
    print(prob2.__doc__)
    print()
    timestats = prob2(db)
    print()

    print(prob3.__doc__)
    print()
    nsig, nbkg = prob3(db)
    print()

    print(prob4.__doc__)
    print()
    ipchi2cut = 13
    dboriginal = db
    db = prob4(db, ipchi2cut)
    print()

    print(prob5.__doc__)
    print()
    dbipchi2cut = db
    db, optcut = prob5(db)
    print()
    plot_mass_after_selection(db, dboriginal, optcut, ipchi2cut)

    print(prob6.__doc__)
    print()
    sigdist, bkgdist = prob6(db)
    print()
    plot_signal_background_time(sigdist, bkgdist)

    # Return everything that's been defined in the local namespace
    return locals()


if __name__ == '__main__':
    vals = main()
    # Update the global namespace with the variables defined in the
    # main function
    globals().update(**vals)
