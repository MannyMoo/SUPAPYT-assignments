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
    nextstudent=$(python3 -c "import os
dirs = list(filter(lambda d : os.path.isdir('../' + d), sorted(os.listdir('..'))))
pwd = os.getcwd().split(os.sep)[-1]
ipwd = dirs.index(pwd)
if ipwd == len(dirs) - 1 :
    print('You\\'re done!')
else :
    print(dirs[ipwd+1])
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
	    eval "$EDITOR $(ls *.py)"
	fi
    fi
}

function how-many-to-go() {
    python3 -c 'import glob,os
dirs = sorted(os.path.split(d)[1] for d in glob.glob("../Participant*"))
print(str(dirs.index(os.path.split(os.getcwd())[1])+1) + "/" + str(len(dirs)))
'
}

function open-grade() {
    open Participant_${1}_assignsubmission_file_/Participant_${1}_MarkingCriteria.pdf
}

function get-grade() {
    # Get the grade for the give participant
    fname=Participant_${1}_assignsubmission_file_/Participant_${1}_MarkingCriteria.ods
    python3 -c "from pandas_ods_reader import read_ods
f = read_ods('$fname', 1)
print(f.iloc[10]['Total grade [%]'])"
}

function get-all-grades() {
    for d in $(ls -d Participant*) ; do
	n=$(echo $d | sed 's/.*\([0-9][0-9][0-9][0-9]\).*/\1/')
	echo -n "$n "
	get-grade $n
    done
}

function grade-stats() {
    python -c "from pandas_ods_reader import read_ods
import os, statistics

grades = []
for d in os.listdir('.'):
    if not d.startswith('Part'):
       continue
    fname = os.path.join(d, 'Participant_' + d.split('_')[1] + '_MarkingCriteria.ods')
    f = read_ods(fname, 1)
    grades.append(f.iloc[10]['Total grade [%]'])
print('Mean grade: {:.2f}%'.format(statistics.mean(grades)))
print('Std dev:    {:.2f}%'.format(statistics.stdev(grades)))
"
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

# Make the feedback .zip file to upload feedback for all students at once
# Execute in the directory containing the .zip file of all submissions
# and the Participant_* directories containing the feedback pdf files.
function make-feedback() {
    mkdir feedback
    cd feedback
    # unzip the original submissions
    unzip ../*.zip
    # copy the pdf feedback files into the submission directories
    for d in $(ls); do
	cp ../$d/*.pdf $d
    done
    # zip them
    zip -r ../feedback.zip Participant_*
    cd ..
    # clean up
    rm -r feedback
}
