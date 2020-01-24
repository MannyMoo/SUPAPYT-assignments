#!/usr/bin/env python

import ROOT

r = ROOT.TRandom3(1234)
with open('small-body-db.csv', 'w') as fout:
    with open('results.csv') as f:
        line = f.readline()
        fout.write(line)
        line = f.readline()
        while line:
            if r.Rndm() < 0.01:
                fout.write(line)
            line = f.readline()
