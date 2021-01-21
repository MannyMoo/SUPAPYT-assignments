from Database import Database
import ROOT
from pprint import pprint

with open('D0KpiData.csv') as inputfile:
    db = Database(csvfile = inputfile)


f = ROOT.TFile('MasterclassData.root')
tree = f.DecayTree

massstats = db.stats('mass')
massstddev = massstats['stddev']
massmin = round(massstats['min'], 0)
massmax = round(massstats['max'], 0)
massmean = massstats['mean']

print('mass min:', massmin, 'max:', massmax, 'mean:', round(massmean, 2), 'stddev:', round(massstddev, 2))


def in_bkg_region(entry):
    return (entry.mass < massmin + massstddev
            or entry.mass > massmax - massstddev)


def in_signal_region(entry):
    return abs(entry.mass - massmean) < massstddev


def count_signal_background(db):
    nbkg = len(db.filter(in_bkg_region))
    nsigregion = len(db.filter(in_signal_region))
    return nsigregion - nbkg, nbkg


def filter_range(db, attr, vmin, vmax):
    test = lambda entry : getattr(entry, attr) >= vmin and getattr(entry, attr) < vmax
    return db.filter(test)


def count_with_cut(db, attr, vmin, vmax = float('inf')):
    cutdb = filter_range(db, attr, vmin, vmax)
    nsig, nbkg = count_signal_background(cutdb)
    return cutdb, nsig, nbkg

def optimise_cut(db, attr, vstart, vend, delta, mincut = True):
    cutdb = db
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
        cutdb, nsig, nbkg = count_with_cut(cutdb, attr, *cutrange(cut))
        try:
            sig = nsig/(nsig + 2*nbkg)**.5
        except ZeroDivisionError:
            sig = 0.
        cutsigs.append([cut, sig])
    return max(cutsigs, key = lambda val : val[1]) + [cutsigs]

def signal_background_distribution(db, attr, nbins, vmin, vmax):
    delta = (vmax - vmin)/nbins
    counts = []
    while vmin < vmax:
        vmaxbin = vmin + delta
        bindb, nsig, nbkg = count_with_cut(db, attr, vmin, vmaxbin)
        counts.append({'nsig' : nsig, 'nbkg' : nbkg, 'vmin' : vmin, 'vmax' : vmaxbin})
        vmin = vmaxbin
    return counts

nsig, nbkg = count_signal_background(db)
print('N. signal:', nsig, 'n. bkg:', nbkg)

print('IP chi2 cut:')

# optipchi2, maxsigipchi2, cutsigsipchi2 = optimise_cut(dboriginal, 'ipchi2', 0, 50, 1, False)
# pprint(cutsigsipchi2)
# print(optipchi2, maxsigipchi2)

for ipmin, ipmax in (13, float('inf')), (0, 13):
    cutdb, nsig, nbkg = count_with_cut(db, 'ipchi2', ipmin, ipmax)
    print('ipmin:', ipmin, 'ipmax:', ipmax)
    print('N. signal:', nsig, 'n. bkg:', nbkg)

dboriginal = db
db = filter_range(db, 'ipchi2', 0, 20)

print('pt cut:')
ptstats = db.stats('pt')
delta = 10
ptcut = ptstats['min']
optcut, maxsig, cutsigs = optimise_cut(db, 'pt', ptstats['min'], 5000, 10)
pprint(cutsigs)

dbipchi2cut = db
db = filter_range(db, 'pt', optcut, float('inf'))
nsigcut, nbkgcut = count_signal_background(db)
print('pt cut:', optcut, 'sig sig:', maxsig, 'nsig:', nsigcut, 'nbkg:', nbkgcut)

timestats = db.stats('decaytime')
tmin = round(timestats['min'], 2)
tmax = round(timestats['max'], 2)

counts = signal_background_distribution(db, 'decaytime', 100, tmin, tmax)
pprint(counts)
print(sum(count['nsig'] * (count['vmin']+count['vmax'])/2. for count in counts)/
      sum(count['nsig'] for count in counts) - tmin)
