import sys
import re

def parseProcStat(statFile):
    ret = {}
    nr_cpu = 0
    with open(statFile,'r') as statf:
        for l in statf.readlines():
            #key [numbers...]
            tup = l.split()
            key = tup[0]
            if re.search('cpu[0-9]+', key):
                nr_cpu += 1
            ret[key] = tup[1:]
    ret["nr_cpu"] = nr_cpu
    return ret

def getCPUUtilization(startCPU, endCPU):
    #[user, nice, system, idle] unit in 10ms
    userTime = (int(endCPU[0]) - int(startCPU[0])) * 10
    systemTime = (int(endCPU[2]) - int(startCPU[2])) * 10
    idleTime = (int(endCPU[3]) - int(startCPU[3])) * 10
    totalTime = userTime + systemTime + idleTime
    busyTime = userTime + systemTime
    utilization = float(busyTime)/totalTime
    return [utilization, totalTime, busyTime, userTime, systemTime, idleTime]

def listCPUUtilization(startStatFile, endStatFile):
    ret= {}
    startStat = parseProcStat(startStatFile)
    endStat = parseProcStat(endStatFile)
    # total CPU    
    totalUsage = getCPUUtilization(startStat['cpu'], endStat['cpu'])
    print("Total Util:%.3f, TotalTime(ms):%d, BusyTime(ms):%d" % (totalUsage[0], totalUsage[1], totalUsage[2]))
    ret["cpu"] = [totalUsage[0], totalUsage[1], totalUsage[2]]
    print("==================================================")
    for i in range(0, startStat['nr_cpu']):
        coreKey = 'cpu'+str(i)
        coreUsage = getCPUUtilization(startStat[coreKey], endStat[coreKey])
        print("Core%d Util:%.3f, TotalTime(ms):%d, BusyTime(ms):%d" % (i, coreUsage[0], coreUsage[1], coreUsage[2]))
        
        ret["cpu%s" %(i)] =  [coreUsage[0], coreUsage[1], coreUsage[2]]
    return ret
if __name__ == '__main__':
    usage = "python parsecpu.py startProcStatFile endProcStatFile"
    if (len(sys.argv) != 3):
        print(usage)
        exit(1)
    listCPUUtilization(sys.argv[1], sys.argv[2]);


    
