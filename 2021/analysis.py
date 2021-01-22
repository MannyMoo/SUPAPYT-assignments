from Database import Database
import ROOT
from pprint import pprint
from matplotlib import pyplot as plt
from matplotlib import patches

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


def plot(db, attr, title, label, savename, ax = plt):
    histo = ax.hist(db.iterator(attr), bins = 100, label = label)
    plt.xlabel(title)
    plt.ylabel('N. candidates')
    plt.savefig(savename)
    return histo
    

def plot_mass(db, label, savename, ax = plt):
    return plot(db, 'mass', 'D0 mass [MeV]', label, savename, ax)


with open('D0KpiData.csv') as inputfile:
    db = Database(csvfile = inputfile)

f = ROOT.TFile('MasterclassData.root')
tree = f.DecayTree

plt.yscale('log')
timehisto = plot(db, 'decaytime', 'D0 decay time [ps]', 'All', 'D0Time-NoCuts.png')
plt.clf()
plt.yscale('linear')

massfig, massax = plt.subplots()
masshisto = plot_mass(db, 'All', 'D0Mass-NoCuts.png', massax)

massstats = db.stats('mass')
massstddev = massstats['stddev']
massmin = round(massstats['min'], 0)
massmax = round(massstats['max'], 0)
massmean = massstats['mean']
print('mass min:', massmin, 'max:', massmax, 'mean:', round(massmean, 2), 'stddev:', round(massstddev, 2))
massstddev *= 0.8

massax.add_patch(patches.Rectangle((massmin, 0), massstddev, max(masshisto[0]),
                                   color = 'red', fill = False, hatch = 'X'))
massax.add_patch(patches.Rectangle((massmax - massstddev, 0), massstddev, max(masshisto[0]),
                                   color = 'red', fill = False, hatch = 'X'))
massax.add_patch(patches.Rectangle((massmean - massstddev, 0), 2*massstddev, max(masshisto[0]),
                                   color = 'blue', fill = False, hatch = 'X'))
plt.savefig('D0Mass-WBoxes.png')
plt.clf()

masshisto = plot_mass(db, 'All', 'D0Mass-NoCuts.png')
                 
timestats = db.print_stats('decaytime')
print('lifetime:', timestats['mean'] - timestats['min'])

nsig, nbkg = count_signal_background(db)
print('N. signal:', nsig, 'n. bkg:', nbkg)

print('IP chi2 cut:')

# optipchi2, maxsigipchi2, cutsigsipchi2 = optimise_cut(dboriginal, 'ipchi2', 0, 50, 1, False)
# pprint(cutsigsipchi2)
# print(optipchi2, maxsigipchi2)

ipchi2cut = 13
for ipmin, ipmax in (ipchi2cut, float('inf')), (0, ipchi2cut):
    cutdb, nsig, nbkg = count_with_cut(db, 'ipchi2', ipmin, ipmax)
    print('ipmin:', ipmin, 'ipmax:', ipmax)
    print('N. signal:', nsig, 'n. bkg:', nbkg)

dboriginal = db
db = filter_range(db, 'ipchi2', 0, ipchi2cut)

print('pt cut:')
ptstats = db.stats('pt')
delta = 10
ptcut = ptstats['min']
optcut, maxsig, cutsigs = optimise_cut(db, 'pt', ptstats['min'], 5000, 10)
pprint(cutsigs)

dbipchi2cut = db
db = filter_range(db, 'pt', optcut, float('inf'))
dbrejected = dboriginal.filter(lambda entry : entry.pt < optcut or entry.ipchi2 > ipchi2cut)

nsigcut, nbkgcut = count_signal_background(db)
print('pt cut:', optcut, 'sig sig:', maxsig, 'nsig:', nsigcut, 'nbkg:', nbkgcut)

massaccepted = plot_mass(db, 'Accepted', 'D0Mass-WithCuts.png')
massrejected = plot_mass(dbrejected, 'Rejected', 'D0Mass-WithCuts.png')
plt.legend()
plt.savefig('D0Mass-WithCuts.png')

timestats = db.stats('decaytime')
tmin = round(timestats['min'], 2)
tmax = round(timestats['max'], 2)

counts = signal_background_distribution(db, 'decaytime', 100, tmin, tmax)
pprint(counts)
tmean = (sum(count['nsig'] * (count['vmin']+count['vmax'])/2. for count in counts)/
         sum(count['nsig'] for count in counts))
tmeansq = (sum(count['nsig'] * ((count['vmin']+count['vmax'])/2.)**2. for count in counts)/
           sum(count['nsig'] for count in counts))
print(tmean - tmin, (tmeansq - tmean**2)**.5)

plt.clf()
timevals = tuple((count['vmin']+count['vmax'])/2. for count in counts)
hsig = plt.plot(timevals, [count['nsig'] for count in counts], label = 'Signal')
hbkg = plt.plot(timevals, [count['nbkg'] for count in counts], label = 'Background')
plt.xlabel('D0 decay time [ps]')
plt.ylabel('Yield')
plt.yscale('log')
plt.legend()
plt.savefig('D0Time-wCuts-SigBkg.png')
