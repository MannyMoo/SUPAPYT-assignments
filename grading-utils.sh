#!/bin/bash

function grades-to-pdf() {
    if [ ! -z "$1" ] ; then
	fname=$1
    else
	fname=MarkingCriteria.ods
    fi
    soffice --convert-to pdf $fname
}

function all-grades-to-pdf() {
    for f in $(find . -name '*.ods') ; do
	cd $(dirname $f)
	grades-to-pdf $(basename $f)
	cd -
    done
}

function next-student() {
    nextstudent=$(python2 -c "import os
dirs = sorted(os.listdir('..'))
pwd = os.getcwd().split(os.sep)[-1]
ipwd = dirs.index(pwd)
if ipwd == len(dirs) - 1 :
    print 'You\\'re done!'
else :
    print dirs[ipwd+1]
")
    if [ "$nextstudent" = "You're done!" ] ; then
	echo $nextstudent
    else
	cd ../$nextstudent
	open *.ods
    fi
}

function how-many-to-go() {
    python -c 'import glob,os
dirs = sorted(os.path.split(d)[1] for d in glob.glob("../Participant*"))
print(str(dirs.index(os.path.split(os.getcwd())[1])+1) + "/" + str(len(dirs)))
'
}

function open-grade() {
    open Participant_${1}_assignsubmission_file_/Participant_${1}_MarkingCriteria.pdf
}
