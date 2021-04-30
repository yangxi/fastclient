#!/bin/bash
port=$1
qps=$2
for ((i=1; i<30;i=i+1)); do
    #    ./sendDupTask 1000 20 ../script/1k.term.tasks 192.168.1.97 7777 7778 > td2_1000_${i} 2>log${i}
    #    ./sendTask 5000 20 ../script/1k.term.tasks 192.168.1.97 $port > td2_1000_${i} 2>log${i}
    ./sendTask $qps 20 ../script/1k.term.tasks 192.168.1.97 $port > td2_1000_${i} 2>log${i}
    python ../script/parseIter.py ./td2_1000_${i} $i
    sleep 2;
done
