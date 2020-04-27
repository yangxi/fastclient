#!/bin/python
import sys
from random import randint

def getTaskId(name):
    f = open(name);
    tasks = [];
    while True:
        task = f.readline();
        if (task == ""):
            break;
        tasks.append(int(task.split(',')[1]))
    f.close();
    return tasks;

if __name__ == "__main__":
    usage = "picktask del orig new"
    if (len(sys.argv)!=4):
        print usage
        exit();
    list = getTaskId(sys.argv[1]);
    print list;
    delfile = {};
    for i in range(0, len(list)):
        delfile[i] = True;
    f = open(sys.argv[2]);
    tasks = [];
    taskid = -1;
    while (True):
        taskid += 1;
        task = f.readline();        
        if (task == ""):
            break;
        if (delfile.has_key(taskid)):
            print "delete %s" % task;
            continue;
        tasks.append(task);        
    print "Rem %d tasks\n" % (len(tasks));
    nr_need = 1000 - len(tasks);
    f.close();
    for i in range(0, nr_need):
        next = randint(0, len(tasks));
        print "Copy taskid %d: %s" %(next, tasks[next])
        tasks.append(tasks[next]);
    print "Now, we have %d tasks\n" % (len(tasks));
        
    f = open(sys.argv[3], 'w');
    for i in range(0, len(tasks)):
        f.write(tasks[i]);
    f.close();
        
        
    
