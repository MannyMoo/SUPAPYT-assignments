#!/usr/bin/env python3

import ROOT, subprocess, os, csv
from csv import DictWriter

url = 'https://opendata.cern.ch/record/401/files/MasterclassData.root'
fname = os.path.split(url)[1]
if not os.path.exists(fname):
    subprocess.call(['wget', url])

f = ROOT.TFile(fname)
tree = f.DecayTree

attrs = {'mass' : lambda tree : tree.D0_MM,
         'decaytime' : lambda tree : tree.D0_TAU*1000.,
         'pt' : lambda tree : tree.D0_PT,
         'ipchi2' : lambda tree : tree.D0_MINIPCHI2}

ranges = {'mass' : (1815, 1915),
          'decaytime' : (0.15, 6.),
          }

with open('D0KpiData.csv', 'w') as fout:
    writer = DictWriter(fout, attrs.keys())
    writer.writeheader()
    for i in range(tree.GetEntries()):
        tree.GetEntry(i)
        vals = {attr : func(tree) for attr, func in attrs.items()}
        inrange = True
        for attr, (vmin, vmax) in ranges.items():
            if vals[attr] < vmin or vals[attr] > vmax:
                inrange = False
                break
        if not inrange:
            continue
        writer.writerow(vals)
