#!/bin/python
import sys
import cStringIO
import random
import codecs
import socket
import Queue
import sys
import time
import threading
import cPickle
import gc
import struct
def loadTaskFile(taskFile):
    termTasks = [];
    for task in open(taskFile).readlines():
        if (task.startswith('#')):
            continue;
        t = task.split('#')[0].strip().split(':')
        queryType = t[0].strip();
        queryTerm = t[1].strip();
        queryAnnotation = t[1]
        termTasks.append((queryType, queryTerm))
    return termTasks
def getTaskPerf(taskFiles, serverHost, serverPort):
    MAX_BYTES = 120
    RECV_BUFFER_SIZE = 103
    tasks = [];
    perf = [];
    for tf in taskFiles:
        tasks.extend(loadTaskFile(tf))
    print("# Total %d tasks. " % len(tasks))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((serverHost, serverPort))
    time.sleep(2);
    for i in range(0, len(tasks)):
        taskId = i
        taskString = str(taskId) + ";" + tasks[i][0] + ":" + tasks[i][1];        
        taskString = taskString + ((MAX_BYTES-len(taskString))*' ')
        print("Send task %s" % taskString)
        send =  sock.send(taskString)
        startTime = time.time();
        if send <= 0:
            raise RuntimeError('Failed to send task %s' % taskString)
        result = ''
        while len(result) < RECV_BUFFER_SIZE:
            result = result + sock.recv(RECV_BUFFER_SIZE - len(result))
        endTime = time.time()
        clientLatency = (endTime - startTime) * 1000
        perf.append(result.split(':'));
        print("%s : %.3f  %s" % (tasks[i][1], clientLatency, perf[taskId]))
    return {"tasks":tasks, "perf":perf}
        
if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("pickTasks.py server port taskfiles")
    serverHost = sys.argv[1]
    serverPort = int(sys.argv[2])
    taskFiles = sys.argv[3:]
    taskPerf = getTaskPerf(taskFiles, serverHost, serverPort)
