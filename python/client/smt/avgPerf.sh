#!/bin/bash

#for bench in self antlr bloat chart eclipse fop hsqldb jython luindex lusearch pmd xalan; do
#for bench in self antlr bloat; do
#for bench in self antlr bloat chart eclipse fop; do
for bench in latency; do
    echo "====parse dacapo ${bench}===="
    python ../script/genBox.py ${bench}cmp_invok*_latency.csv > ${bench}_cmp_perf;
    python ../script/genBox.py ${bench}smt_invok*_latency.csv > ${bench}_smt_perf;
    python ../script/genBox.py ${bench}opt_invok*_latency.csv > ${bench}_opt_perf;
	# if [ $bench == "self" ]; then
	#     	python /home/yangxi/benchmark/lucene/util/dacapoDynamic/type0and3/genBox.py ${bench}_invok*_* > ${bench}_RT_perf;
	# else
	#     python /home/yangxi/benchmark/lucene/util/dacapoDynamic/type0and3/genBox.py ${bench}_invok*_* > ${bench}_RT_perf;
	# fi
done
