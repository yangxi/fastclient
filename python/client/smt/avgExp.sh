#!/bin/bash

for bench in self antlr bloat chart eclipse fop hsqldb jython luindex lusearch pmd xalan; do
#for bench in self antlr bloat; do
#for bench in self antlr bloat chart eclipse fop; do
#for bench in self; do
    echo "====parse dacapo ${bench}===="
    python ../script/genAverage.py ${bench}_invok* > ${bench}cmp_average
done
