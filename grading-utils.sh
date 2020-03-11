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
	ipynb="$(ls *.ipynb 2> /dev/null)"
	if [ ! -z "$ipynb" ] ; then
	    jupyter notebook $ipynb&
	else
	    e *.py&
	fi
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

# Should be executed in the directory containing the submission directories Participant_NNNN_.*
# First argument is the marking criteria spreadsheet.
function cp-marking-criteria() {
    crit=$1
    for d in $(find . -mindepth 1 -maxdepth 1 -type d) ; do
	d=$(basename $d)
	dest=$(echo $d | sed 's/\(Participant_[0-9]*\)_.*/\1_MarkingCriteria.ods/')
	cp $crit $d/$dest
    done
}

# Should be executed in the directory containing the submission directories Participant_NNNN_.*
# First argument is the input file.
function cp-input-file() {
    fname=$(abspath $1)
    bname=$(basename $fname)
    for d in $(find . -mindepth 1 -maxdepth 1 -type d) ; do
	dest=$d/$bname
	if [ ! -e $dest ] ; then
	    ln -s $fname $dest
	fi
    done
}
