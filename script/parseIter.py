import sys
import json
import numpy as np
import scipy as sp
from scipy import stats as st
import operator
from struct import *
import bisect
import math
import scipy.stats as stat
import datetime;
import os

#    self.current.write(struct.pack('fffIB', timestamp, latencyMS, queueTimeMS, totalHitCount, len(taskString)))

def ci(D):
    s = np.array(D);
    n, min_max, mean, var, skew, kurt = st.describe(s)
    std=math.sqrt(var)

    #note these are sample standard deviations
    #and sample variance values
    #to get population values s.std() and s.var() will work


    #The location (loc) keyword specifies the mean.
    #The scale (scale) keyword specifies the standard deviation.

    # We will assume a normal distribution
    R = st.norm.interval(0.05,loc=mean,scale=std)
    return R;

def norfreq_to_timefreq(nfreq):
    bin_array = nfreq[0];
    bin_time = np.array(nfreq[0]) * np.array(nfreq[1]);
    total_time = np.sum(bin_time);
    bin_time_freq = bin_time / total_time
    accu_time = 0;
    accu_array = []
    revers_accu_array = []

    for i in range(0, len(bin_array)):
        revers_accu_array.append(1 - accu_time);
        accu_time += bin_time_freq[i];
        accu_array.append(accu_time);

    return [bin_array, bin_time_freq, accu_array, revers_accu_array]




def parse_header_line(l):
    typeToDesc={"long":"Q", "int":"I", "byte":"b", "float":"f", "unsigned char":"B"};
    typeToSize={"long":8, "int":4, "byte":1, "float":4, "unsigned char":1};
    d = {}
    t = "="
    s = 0;
    a = l.strip('#').rstrip('\n').split(',')
    for i in range(0, len(a)):
        kv = a[i].split('->')
        d[kv[0]]=i+1;
        t += typeToDesc[kv[1]];
        s += typeToSize[kv[1]];
    print "this file has keys " + str(d.keys()) + " line size " + str(s) + " parse with " + t;
    return (d, t, s);

def update_latency_stat(stat,latency):
    for k in latency:
        stat[k].append(latency[k]);

def latency(vals):
    average_latency = np.average(vals);
    sorted_vals = sorted(enumerate(vals),key=lambda i:i[1])
#    sorted_vals = sorted(vals);
    mean_index = int(len(sorted_vals)*0.5)
    per_95_index = int(len(sorted_vals)*0.95)
    per_99_index = int(len(sorted_vals)*0.99)
    return {"avg":average_latency, "50":sorted_vals[mean_index][1], "95":sorted_vals[per_95_index][1], "99":sorted_vals[per_99_index][1], "perc_index":[sorted_vals[mean_index][0],sorted_vals[per_95_index][0],sorted_vals[per_99_index][0]]};

#return [50% 90 99 max]
def get_tail_latency(time, cols, key_col):
    nr_tasks = len(time);
    sorted_index = np.argsort(time);
    sorted_client_time = np.sort(time);
    median_index = int(nr_tasks * 0.5) - 1;
    p90_index = int(nr_tasks * 0.9) - 1;
    p99_index = int(nr_tasks * 0.99) - 1;
    max_index =  -1;
    return [sorted_client_time[median_index], sorted_client_time[p90_index], sorted_client_time[p99_index], sorted_client_time[max_index]]
#    print "%d %d %d %d\n" % ();
#    print "total %d tasks" % (nr_tasks);    
 

def report_distribution(fname, client_time, cols, key_col):
    nr_tasks = len(client_time);
    sorted_index = np.argsort(client_time);
    sorted_client_time = np.sort(client_time);

    print "total %d tasks" % (nr_tasks);    
    median_index = int(nr_tasks * 0.5) - 1;
    p90_index = int(nr_tasks * 0.9) - 1;
    p99_index = int(nr_tasks * 0.99) - 1;
    max_index =  -1;
    print "%d %d %d %d\n" % (sorted_client_time[median_index], sorted_client_time[p90_index], sorted_client_time[p99_index], sorted_client_time[max_index]);
        #x is ms, y is % of requrest
    dist_file_name = fname + '-dist.csv';
    f = open(dist_file_name, 'w');
#    f = open('./''./client-time-dist.csv', 'w');
    client_time_freq = norfreq(client_time)
    client_time_dist = norfreq_to_timefreq(client_time_freq);
    for i in range(0, len(client_time_dist[0])):
        f.write("%d,%.3f,%.3f\n" % (client_time_dist[0][i],client_time_dist[1][i] * 100,client_time_dist[2][i]* 100));
    f.close()

    top10_file_name = fname +'-top30.csv';
    f = open(top10_file_name, 'w');
    for ri in range(nr_tasks - 30, nr_tasks):        
        client = sorted_client_time[ri]
        client_index = sorted_index[ri]
        taskid = cols[key_col["taskid"]][client_index];
        clientlatency = cols[key_col["clientLatency"]][client_index];
        serverlatency = cols[key_col["serverLatency"]][client_index];
        serverqtime = cols[key_col["queueTime"]][client_index];
        cputime = cols[key_col["cpuTime"]][client_index];
        ipc = cols[key_col["IPC"]][client_index];
        f.write("%d,%d,%d,%d,%d,%d,%d\n" % (ri, taskid, clientlatency, serverlatency, serverqtime, cputime, ipc))
    f.close();
    top10_file_name = fname +'-1ms.csv';    
    f = open(top10_file_name, 'w');
    for ri in range(0, nr_tasks):        
        client = sorted_client_time[ri]
        client_index = sorted_index[ri]
        taskid = cols[key_col["taskid"]][client_index];
        clientlatency = cols[key_col["clientLatency"]][client_index];
        serverlatency = cols[key_col["serverLatency"]][client_index];
        serverqtime = cols[key_col["queueTime"]][client_index];
        cputime = cols[key_col["cpuTime"]][client_index];
        ipc = cols[key_col["IPC"]][client_index];
        if (serverlatency > 1000):            
            f.write("%d,%d,%d,%d,%d,%d,%d\n" % (ri, taskid, clientlatency, serverlatency, serverqtime, cputime, ipc))
    f.close();

def parse_log(fname, reportDist=False):
#{col_num:"str"}
    col_key={}
    key_col={}
#[in column view]
    cols=[];
    diff_cols=[]
#[in raw view]
    raws=[];
    iters_index = [];

    f = open(fname,'r');
    hl = f.readline();
#    hl = "#taskid:hits:receiveStamp:queueTime:finishTime:retiredIns:retiredCycles:clienttime:serverQtime:serverPtime:serverLatency\n"
    hl = "#taskid:hits:receiveStamp:queueTime:serverLatency:retiredIns:retiredCycles:clientLatency:clientSendStamp:clientRecvStamp:serverPtime:cpuTime:IPC\n"
    a = hl.strip('#').rstrip('\n').split(':')
    for i in range(0, len(a)):
        col_key[i] = a[i];
        key_col[a[i]] = i;
    for i in col_key.keys():
        cols.append([]);
    while True:
        r = f.readline().rstrip('\n').split(':');
        if (r[0] == ''):
#            print "finished passing the log"
            break;
        for i in range(0, len(r)):
            try:
                r[i] = int(r[i]);
            except ValueError:
                r[i] = float(r[i]);
        raws.append(r);
        for j in range(0, len(r)):
            cols[j].append(r[j]);
#?
#    nr_iters = len(raws) / 1141;
#    for i in range(0, nr_iters):
#        iters_index.append(i * 1141);

# turn clienttime to a np vector
    cols[key_col["clientLatency"]] = np.array(cols[key_col["clientLatency"]]);
# serverQtime, serverPtime, and serverLatency are in MS
    cols[key_col["serverLatency"]] = (np.array(cols[key_col["serverLatency"]])/(1000.0));
    cols[key_col["queueTime"]] = (np.array(cols[key_col["queueTime"]])/(1000.0));
    cols[key_col["cpuTime"]] = np.array(cols[key_col["retiredCycles"]])/(2100.0)
    cols[key_col["serverPtime"]] = cols[key_col["serverLatency"]] - cols[key_col["queueTime"]];
    cols[key_col["IPC"]] = np.array(cols[key_col["retiredIns"]]) * 1.0 / np.array(cols[key_col["retiredCycles"]]);
# The CPU is running at 2.1GHz

#    cpuPtime = np.array(cols[key_col["retiredCycles"]])/(2100.0)

    # dump all requests to a file
    # f = open('./rtime.csv', 'w')
    # f.write("#no id clientlatency serverlatency serverPtime serverQtime cpuTime IPC\n");
    # for i in range(0, len(cols[key_col["taskid"]])):
    #     f.write("%d,%d,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n" % (i+1, cols[key_col["taskid"]][i], cols[key_col["clientLatency"]][i], cols[key_col["serverLatency"]][i], cols[key_col["serverPtime"]][i], cols[key_col["queueTime"]][i], cols[key_col["cpuTime"]][i], cols[key_col["IPC"]][i]));
    # f.close();

    #now we want to compute a histogram about the time
    # in total, we have 20,000 requrests (20 iterations of 1k requrest)
    #x [1-100] represents percentable of requests
    #y: x% requests finished lower than y(ms)
#    for i in range(0, len(server_time)):
#        if (server_time[i] > 1000):
#            print "%d: %d" % (task_id[i], server_time[i]);

    if (reportDist):
        client_time = cols[key_col["clientLatency"]].astype(int)
        server_time = cols[key_col["serverLatency"]].astype(int)/100;
        task_id = cols[key_col["taskid"]];
        report_distribution('./client-time', client_time, cols, key_col);
        report_distribution('./server-time', server_time, cols, key_col);
        f = open('./client-IPC.csv', 'w');
        ipc = cols[key_col["IPC"]];        
        for ri in range (0, len(ipc)):
            f.write("%d,%.3f,%d,%d\n"%( ri, ipc[ri], client_time[ri], server_time[ri]));
        f.close();
    # nr_tasks = len(client_time);
    # sorted_index = np.argsort(client_time);
    # sorted_client_time = np.sort(client_time);
    #     #x is ms, y is % of requrest
    # f = open('./client-time-dist.csv', 'w');
    # client_time_freq = norfreq(client_time)
    # client_time_dist = norfreq_to_timefreq(client_time_freq);
    # for i in range(0, len(client_time_dist[0])):
    #     f.write("%d, %.3f, %.3f\n" % (client_time_dist[0][i],client_time_dist[1][i] * 100,client_time_dist[2][i]* 100));
    # f.close()

    # f = open('./client-time-top10.csv', 'w');
    # for ri in range(nr_tasks - 10, nr_tasks):        
    #     client = sorted_client_time[ri]
    #     client_index = sorted_index[ri]
    #     taskid = cols[key_col["taskid"]][client_index];
    #     clientlatency = cols[key_col["clientLatency"]][client_index];
    #     serverlatency = cols[key_col["serverLatency"]][client_index];
    #     serverqtime = cols[key_col["queueTime"]][client_index];
    #     cputime = cols[key_col["cpuTime"]][client_index];
    #     ipc = cols[key_col["IPC"]][client_index];
    #     f.write("%d,%d,%.2f,%.2f,%.2f,%.2f,%.2f\n" % (ri, taskid, client, serverlatency, serverqtime, cputime, ipc))
    # f.close();
    
#     f = open('./client-time-max.csv', 'w');
#     # print top t0
#     
#     for i in range(nr_tasks-10, nr_tasks):
        
#     f.write("#percent #id #client #server #serverq #cputim\n");
# #    for i in range(99, -1, -1):
#     for i in range(0, 100):
#         ri = (i+1)*200 - 1
#         ri_base = i*200;
#         ri_top  = (i+1)*200;
#         client = sorted_client_time[ri]
#         client_index = sorted_index[ri]
#         taskid = cols[key_col["taskid"]][client_index];
#         serverlatency = cols[key_col["serverLatency"]][client_index];
#         serverqtime = cols[key_col["serverQtime"]][client_index];
#         #computer averageqtime
#         sum_server_qtime = 0;
#         for qindex in range(ri_base,ri_top):
#             server_index = sorted_index[qindex];
#             this_server_time = cols[key_col["serverQtime"]][server_index]
#             sum_server_qtime += this_server_time;
#         avg_server_qtime = sum_server_qtime / (ri_top - ri_base);
#         cputime = cpuPtime[client_index];
#         f.write("%d,%d,%.2f,%.2f,%.2f,%.2f,%.2f\n" % (i+1, taskid, client, serverlatency, serverqtime, cputime, avg_server_qtime))
#     f.close();

    #marsk retiredCycles and retiredIns
    # cycle_index = key_col["retiredCycles"];
    # cycle_col = cols[cycle_index]
    # cols[cycle_index] = np.array(cycle_col) & (0xffffffff);

    # ins_index = key_col["retiredIns"];
    # ins_col = cols[ins_index]
    # cols[ins_index] = np.array(ins_col) & (0xffffffff);

    # for i in range(0, len(cols)):
    #     c = cols[i];
    #     diff_c = np.array(c[1:]) - np.array(c[0:-1]);
    #     for i in range(0, len(diff_c)):
    #         if (diff_c[i] < 0):
    #             diff_c[i] = 0xffffffff + diff_c[i];
    #     diff_cols.append(diff_c);
#    print "%ld - %ld = %ld" % (cols[3][1],cols[3][0], diff_cols[3][0]);
#    return {"col_key":col_key,"key_col":key_col,"cols":cols, "diff_cols":diff_cols,"raws":raws};
    return {"col_key":col_key,"key_col":key_col,"cols":cols,"raws":raws};




#input:a list, out put:[bin,percent,accupercent]
def norfreq(a):
    fa = stat.itemfreq(a)
    t = len(a)
    sfa = np.hsplit(fa,2)
    sfa[1] = sfa[1].astype(float)/t;

    x=[];y=[];z=[]
    tz = 0;
    for i in range(0, len(sfa[0])):
        k = sfa[0][i][0]
        v = sfa[1][i][0]
        x.append(k)
        y.append(v)
        tz += v
        z.append(tz);
    return [x,y,z]



#{key->count}
def parse_lucene_iter(parsed_log):
    #process time distribution, latency distribution, queue time distribution
    print parsed_log["key_col"];
    cols = parsed_log["cols"]
    raws = parsed_log["raws"]
#    diff_cols = parsed_log["diff_cols"]
    receive_stamp_index = parsed_log["key_col"]["receiveStamp"]
    process_stamp_index = parsed_log["key_col"][""];
    finish_stamp_index = parsed_log["key_col"]["finishStamp"];
    cycle_index = parsed_log["key_col"]["retiredCycles"];
    instruction_index = parsed_log["key_col"]["retiredIns"];

#    ptimeMS = cols[finish

    ptimeNS = np.array(cols[finish_stamp_index]) - np.array(cols[process_stamp_index]);
    ptimeMS = ptimeNS/(1000*1000);
    ptime_hist = norfreq(ptimeMS);
    ptime_time_hist = norfreq_to_timefreq(ptime_hist);
    ptime_perc = latency(ptimeNS);

    ltimeNS = np.array(cols[finish_stamp_index]) - np.array(cols[receive_stamp_index]);
    ltimeMS = ltimeNS/(1000*1000);
    ltime_hist = norfreq(ltimeMS);
    ltime_perc = latency(ltimeNS);
    ctimeCol = parsed_log["key_col"]["clienttime"];
    ctimeMS = np.array(cols[ctimeCol]);
    print ctimeMS;
    ctime_hist = norfreq(ctimeMS);
    ctime_perc = latency(ctimeMS);



    idletimeNS = diff_cols[process_stamp_index] * 2 - diff_cols[cycle_index];
#    print diff_cols[process_stamp_index][0:10]
#    print diff_cols[cycle_index][0:10]
#    print idletimeNS[0:10]
#    for i in range(0,len(idletimeNS)):

        # if (idletimeNS[i] < 0):
        #     print "[%d %d] %d %s %s %s\n" % (diff_cols[process_stamp_index][i], diff_cols[cycle_index][i],i, str(raws[i]), str(raws[i+1]), str(np.array(raws[i+1])-np.array(raws[i])));
        # if (idletimeNS[i] > 1000000):
        #     l = "+%d--" % i;
        #     for j in range(0,10):
        #         l += ",[%d,%d,%d] " % (idletimeNS[i+j], ptimeMS[i+j+1], ltimeMS[i+j+1])
        #     print l
        # if (idletimeNS[i] < 5000):
        #     print "-%d---%s,%s,%s\n" % (i, idletimeNS[i],idletimeNS[i+1],idletimeNS[i+2]);
    idletimeUS = idletimeNS/(1000)
#    print idletimeUS[0:10]
    idletime_hist = norfreq(idletimeUS);
    idletime_perc = latency(ltimeNS);

#    ipkc = np.array(diff_cols[instruction_index]) * 1000 / np.array(diff_cols[cycle_index]);
#    for i in range(0, len(ipkc)):
#        print "%d : %d, %d" % (i, ipkc[i], ptimeMS[i])
    ipkc = (np.array(cols[cycle_index]) * 1000)/np.array(cols[instruction_index]);
    ipkc_hist = norfreq(ipkc);
    ipkc_perc = latency(ipkc);

    #idle report




#    print ltime_perc;
#    for i in range(0, len(ltimeNS)):
#        if (ltimeNS[i] >= ltime_perc["99"]):
#            print "id:%d -> ptime %d, ltime %d diff %s" % (raws[i][0],ptimeMS[i], ltimeMS[i], np.array(raws[i]) - np.array(raws[i-1]));


    return {"ctime_hist":ctime_hist, "ctime_perc":ctime_perc, "ptime_time_hist":ptime_time_hist, "ptime_hist":ptime_hist,"ptime_perc":ptime_perc,"ltime_hist":ltime_hist,"ltime_perc":ltime_perc,"idletime_hist":idletime_hist,"idletime_perc":idletime_perc, "ipkc_hist":ipkc_hist,"ipkc_perc":ipkc_perc};


detailedMode = False;

def parse_lucene_log(fname, expected_qps, expected_iter):
    global detailedMode;
#let's calculate process time distribution
    parsed_log = parse_log(fname, detailedMode);
#        nr_iters = len(parsed_log["iters"]);
    nr_tasks = len(parsed_log["raws"]);
    client_send_stamp_index =  parsed_log["key_col"]["clientSendStamp"];
    client_recv_stamp_index =  parsed_log["key_col"]["clientRecvStamp"];
    client_time_index = parsed_log["key_col"]["clientLatency"];
    server_time_index = parsed_log["key_col"]["serverLatency"];    
    cols = parsed_log["cols"];
    wall_total_cycle = (cols[client_send_stamp_index][-1] - cols[client_send_stamp_index][0])
    wall_total_sec = wall_total_cycle / (2100.0 * 1000 * 1000);
    avg_qps = float(nr_tasks)  / wall_total_sec;

    # report results
    client_time_us = cols[client_time_index].astype(int);
    server_time_us = cols[server_time_index].astype(int);
    client_tail = get_tail_latency(client_time_us, cols, parsed_log["key_col"]);
    server_tail = get_tail_latency(server_time_us, cols, parsed_log["key_col"]);
    client_50th_ms = client_tail[0]/(1000.0)
    client_90th_ms = client_tail[1]/(1000.0)
    client_99th_ms = client_tail[2]/(1000.0)
    client_max_ms = client_tail[3]/(1000.0)

    server_50th_ms = server_tail[0]/(1000.0)
    server_90th_ms = server_tail[1]/(1000.0)
    server_99th_ms = server_tail[2]/(1000.0)
    server_max_ms = server_tail[3]/(1000.0)
    print "%d,%d,%d,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f" % (expected_iter, expected_qps, int(avg_qps),
                                                                client_50th_ms,client_90th_ms,client_99th_ms,client_max_ms,
                                                                server_50th_ms,server_90th_ms,server_99th_ms,server_max_ms);
                                                                
    # cycles_index = parsed_log["key_col"]["retiredCycles"];
    # client_time = parsed_log["key_col"]["clienttime"];
    # raws = parsed_log["raws"]
    # cols = parsed_log["cols"]
    # wall_total_cycle = cols[rc_stamp_index][-1] - cols[rc_stamp_index][0];
    # wall_total_sec = wall_total_cycle/(1000000000.0);
 
# observed QPS
#    print "Tasks:%d, cycles:%d, qps:%.2f (%d)\n" % (nr_tasks, wall_total_cycle, avg_qps, expected_qps);
    stat = {};
    stat["measured_qps"] = avg_qps;
    return stat;
# CPU utilization
    # diff_cycle_col = parsed_log["diff_cols"][cycles_index]
    # nr_cycles = np.sum(diff_cycle_col);
    # nr_wall_cycles = cols[process_stamp_index][-1] - cols[process_stamp_index][0]
    # utilization = nr_cycles/(nr_wall_cycles * 2.0);
    # print "total cycles:%d, total wall cycles:%d, utilization:%f\n" % (nr_cycles, nr_wall_cycles * 2, utilization);
    # stat =  parse_lucene_iter(parsed_log); 
#    stat["utilization"] = utilization;


# process t


    # #stats{qtime:{"avg":[iter0,....,iterN],"mean":[],"}}
    # qtime_stat = {"avg":[],"mean":[],"95":[],"99":[]}
    # ptime_stat = {"avg":[],"mean":[],"95":[],"99":[]}
    # ltime_stat = {"avg":[],"mean":[],"95":[],"99":[]}

    # stats = {"qtime":qtime_stat, "ptime":ptime_stat, "ltime":ltime_stat}
    # avgs = {"qtime":{}, "ptime":{}, "ltime":{}}
    # for i in range(0, len(iters_index)):
    #     start_index = iters_index[i];
    #     end_index = start_index + nr_tasks;
    #     qtime_latency = latency(cols[3][start_index:end_index]);
    #     update_latency_stat(qtime_stat, qtime_latency);
    #     ptime_latency = latency(cols[4][start_index:end_index]);
    #     update_latency_stat(ptime_stat, ptime_latency);
    #     ltime_latency = latency(np.array(cols[3][start_index:end_index]) + np.array(cols[4][start_index:end_index]))
    #     update_latency_stat(ltime_stat, ltime_latency);
    # for t in stats.keys():
    #     for l in stats[t].keys():
    #         avgs[t][l] = [np.average(stats[t][l]),ci(stats[t][l])]
    # return (col_key, raws, cols, stats, avgs)

#each file name in format as
#id_qps_iteration
def parse_logs(names):
    logs = {}
    for f in names:
        sf = f.split('_');
        iters = int(sf[-1])
        qps = int(sf[-2])
        print "parse log file %s qps %d invoks %d\n" %(f, qps, iters)
        logs[qps] = parse_lucene_log(f, qps, iters)
    return logs

def parse_iteration(f, iter):
    sf = f.split('_');
#    iters = int(sf[-1])
    qps = int(sf[-2])
#    print "parse log file %s qps %d interation %d\n" %(f, qps, iter)
    log = parse_lucene_log(f, qps, iter)
    return log;


if __name__ == "__main__":
    usage = "python logfile iteration"
#    if (len(sys.argv) < 2):
#        print usage
#        exit()
    if (len(sys.argv) < 3):
        print usage
        exit()
#    print sys.argv
    iter = int(sys.argv[2]);    
    if (len(sys.argv) > 3):
        detailedMode = True;
    log = parse_iteration(sys.argv[1], iter)
    #output qps-latency.csv

    # f = open('./ptime-time-dist.csv', 'w')
    # qps = sorted(logs.keys())[0];
    # f.write("#timestamp:%s bin qps %d, percentage_time, accumulated_time\n" % (datetime.datetime.now(),qps));
    # ptime_dist = logs[qps]["ptime_time_hist"];
    # for i in range(0, len(ptime_dist[0])):
    #     f.write("%d, %.3f, %.3f\n" % (ptime_dist[0][i],ptime_dist[1][i],ptime_dist[2][i]));
    # f.close()


# if __name__ == "__main__":
#     usage = "python logfile qps-latency.csv"
#     if (len(sys.argv) < 2):
#         print usage
#         exit()
#     fnames=[]
#     logs = parse_logs(sys.argv[1:])
#     #output qps-latency.csv

#     f = open('./ptime-time-dist.csv', 'w')
#     qps = sorted(logs.keys())[0];
#     f.write("#timestamp:%s bin qps %d, percentage_time, accumulated_time\n" % (datetime.datetime.now(),qps));
#     ptime_dist = logs[qps]["ptime_time_hist"];
#     for i in range(0, len(ptime_dist[0])):
#         f.write("%d, %.3f, %.3f\n" % (ptime_dist[0][i],ptime_dist[1][i],ptime_dist[2][i]));
#     f.close()

#     # f = open('./rtime.csv', 'w')
#     # q = logs.keys()[0];
#     # clienttime_index = logs[q]["log"]["key_col"]["clienttime"]
#     # clienttime_data = logs[q]["log"]["cols"][clienttime_idnex];
#     # serverlatency_index = logs[q]["log"]["key_col"]["server"]

# #how many requests we have
#     if (True):
#         f = open('./qps-latency.csv', 'w');
#         f.write("#timestamp:%s qps,realqps,ptime_50latency,ptime_95latency,ltime_50,ltime_95,CPU utiliztion,IPC\n" % datetime.datetime.now());
#         bl = ""
#         for qps in sorted(logs.keys()):
#             realqps = logs[qps]["measured_qps"];
#             cpu_util = logs[qps]["utilization"];
#             ipc = logs[qps]["ipkc_perc"]["50"];
#             ptime_50 = logs[qps]["ptime_perc"]["50"]/(1000.0*1000);
#             ptime_95 = logs[qps]["ptime_perc"]["95"]/(1000.0*1000);
#             ptime_99 = logs[qps]["ptime_perc"]["99"]/(1000.0*1000);
#             ltime_50 = logs[qps]["ltime_perc"]["50"]/(1000.0*1000);
#             ltime_95 = logs[qps]["ltime_perc"]["95"]/(1000.0*1000);
#             ltime_99 = logs[qps]["ltime_perc"]["99"]/(1000.0*1000);
#             ctime_50 = logs[qps]["ctime_perc"]["50"];
#             ctime_95 = logs[qps]["ctime_perc"]["95"];
#             ctime_99 = logs[qps]["ctime_perc"]["99"];
#             bl += " [%d]=%d " %(qps,100-ltime_99);
#             f.write("%d,%d,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%.3f,%d\n" % (qps,realqps,ptime_50,ptime_95,ptime_99,ltime_50,ltime_95,ltime_99,ctime_50,ctime_95,ctime_99,cpu_util,ipc));
#         f.write("#budgets=( %s )\n" %bl);
#         for qps in sorted(logs.keys()):
#             f.write("#ltime_per_index=" + str(logs[qps]["ltime_perc"]["perc_index"]) + " ptime_index " + str(logs[qps]["ptime_perc"]["perc_index"]) + " \n");
#         f.close()

#     if (True):
#         f = open('./ptime-dist.csv', 'w')
#         f.write("#timestamp:%s bin, percentage, accumulated percentage\n" % datetime.datetime.now());
#         ptime_dist = logs[qps]["ptime_hist"];
#         for i in range(0, len(ptime_dist[0])):
#             f.write("%d, %.3f, %.3f\n" % (ptime_dist[0][i],ptime_dist[1][i],ptime_dist[2][i]));
#         f.close()


#     if (True):
# #    if (os.path.isfile('./idletime-dist.csv') == False):

#         f = open('./idletime-dist.csv', 'w')
#         f.write("#QPS:120 timestamp:%s bin, percentage, accumulated percentage\n" % datetime.datetime.now());
#         ptime_dist = logs[qps]["idletime_hist"];
#         for i in range(0, len(ptime_dist[0])):
#             f.write("%d, %.3f, %.3f\n" % (ptime_dist[0][i],ptime_dist[1][i],ptime_dist[2][i]));
#         f.close()
