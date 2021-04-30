#!/bin/bash

NR_INVOK=20
if [ -n "$1" ]
then
    NR_INVOK=$1
    echo "Handle $NR_INVOK invocations";
fi

#for bench in self antlr bloat chart eclipse fop hsqldb jython luindex lusearch pmd xalan; do
#for bench in chart eclipse fop hsqldb jython luindex lusearch pmd xalan; do
#for bench in self antlr bloat chart eclipse fop; do
#for bench in self antlr bloat; do
for bench in latency; do
#for bench in self chart; do
    echo "====parse dacapo ${bench}===="
    for ((i=1;i<=${NR_INVOK};i=i+1)); do
	echo "${bench} invocation${i}";
	python ../script/parseTasks.py ./${bench}cmpInvok${i}_*_20;
	cp qps-latency.csv ${bench}cmp_invok${i}_latency.csv;
	cp client-time-max.csv ${bench}cmp_invok${i}_taillatency.csv;
	cp top200.csv ${bench}cmp_invok${i}_top200.csv;
    done
done
