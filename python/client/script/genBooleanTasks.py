#!/bin/bash
import sys
import random

def pick(taskFile, numberOrTask, numberAndTask):
    termTasks = [];
    for task in open(taskFile).readlines():
        if (task.startswith('#')):
            continue;
        t = task.split('#')[0].strip().split(':')
        queryType = t[0].strip();
        queryTerm = t[1].strip();
        termTasks.append((queryType, queryTerm))
    print("#%d queries in the file %s" %(len(termTasks), taskFile))
    for i in range(0, numberOrTask):
        term1Index = random.randint(0, len(termTasks)-1)
        term2Index = random.randint(0, len(termTasks)-1)
        newQuery = "Or" + termTasks[term1Index][0] + termTasks[term2Index][0] + ":"+ termTasks[term1Index][1] + " " + termTasks[term2Index][1]
        print(newQuery);

    for i in range(0, numberAndTask):
        term1Index = random.randint(0, len(termTasks)-1)
        term2Index = random.randint(0, len(termTasks)-1)
        newQuery = "And" + termTasks[term1Index][0] + termTasks[term2Index][0] + ":"+ "+" + termTasks[term1Index][1] + " +" + termTasks[term2Index][1]
        print(newQuery);    
    
        

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("genBooleanTasks.py taskFile nrOrTasks nrAndTasks\n")
        exit(1)
    taskFile = sys.argv[1]
    numberOrTask = int(sys.argv[2]);
    numberAndTask = int(sys.argv[3]);
    pick(taskFile, numberOrTask, numberAndTask)
    
    
