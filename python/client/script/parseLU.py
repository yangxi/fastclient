# Parsing and plotting latency and utilization results
import os
from .parseIter import parse_iteration
from .parsecpu import parse_utilization
from matplotlib import pyplot as plt


# @exp_dir: directory of experiment results
# @exps: a list of experiment names, e.g. ["16cputime", "8cputime", "8x1", "4x2"]
# return exp: {"dir": exp_dir, qps:[], latency:{}, util:{}}
# {""}
def parseLU(exp_dir, exps, startQPS, endQPS, qpsStep):
    if not os.listdir(exp_dir):
        return {"error":"The experiment directory, %s, does not exist"%(exp_dir)}
    expQPSs = []
    for q in range(startQPS, endQPS + qpsStep, qpsStep):
        expQPSs.append(q)
    latency={}
    util={}
    for exp in exps:
        exp_lat = {}
        exp_util = {}
        for qps in expQPSs:
            expFileName = "%s/%s_%s_1"%(exp_dir,exp, str(qps))
            expUtilStartName = "%s/ProcStatBegin_%s_%s_1"%(exp_dir, exp, qps)
            expUtilEndName = "%s/ProcStatEnd_%s_%s_1"%(exp_dir, exp, qps)
            l = parse_iteration(expFileName, 1)[0]
            u = parse_utilization(expUtilStartName, expUtilEndName)
            exp_lat[qps] = l
            exp_util[qps] = u
        latency[exp] = exp_lat
        util[exp] = exp_util
    # add the column view 
    latency_col = rowToCol(latency)
    util_col = rowToCol(util)
    ret =  {"dir":exp_dir, "exp":exps, "qps":expQPSs, "latency":latency, "util":util, "latency_col":latency_col, "util_col":util_col}
    return ret

# latency: {'exp': { qps: {client_50th: number, client_90th....: number} } }
# util: {'exp':{qps:{"cpu":[utilization,totaltime(ms),busytime(ms)]}}}
# rowToCol turns the row view to {'exp':{'row_key':[], 'row':[]}
def rowToCol(result):
    cols = {}
    for exp in result.keys():
        print("Process expriment %s" % (exp))
        exp_result = result[exp]
        rows = {}
        col_view = {}
        row_key = result[exp].keys()
        row_key = sorted(row_key)
        col_view["row_key"] = row_key
        item_key = exp_result[row_key[0]].keys()
        print("Item keys: %s" % (item_key))
        for item_key in item_key:
            print("Process column %s" % (item_key))
            rval = []
            for rkey in row_key:
                v = exp_result[rkey][item_key]
                if type(v) is list:
                    rval.append(v[0])
                else:
                    rval.append(exp_result[rkey][item_key])
            rows[item_key] = rval
        col_view['row'] = rows
        cols[exp] = col_view
    return cols
    
def plotExperiments(exp_dir, exps, startQPS, endQPS, qpsStep):
    exp_result = parseLU(exp_dir, exps, startQPS, endQPS, qpsStep)
    plotLU(exp_result)
    return exp_result

def plotLU(exp_result):    
    lat_c = exp_result["latency_col"]
    util_c = exp_result["util_col"]
    # plot the 99th latency
    plt.subplot(4,1,1)
    legend=[]
    for exp in lat_c.keys():
        exp_lat = lat_c[exp]
        l = plt.plot(exp_lat["row_key"], exp_lat["row"]['client_99th'], 'o-', label=exp)
    legend.append(l)
    plt.xlabel("QPS")
    plt.ylabel("99th% latency (ms)")
    plt.legend()
    # plot the 50th latency
    plt.show()
    plt.subplot(4,1,2)
    legend=[]
    for exp in lat_c.keys():
        exp_lat = lat_c[exp]
        l = plt.plot(exp_lat["row_key"], exp_lat["row"]['client_50th'], 'o-', label=exp)
    legend.append(l)
    plt.xlabel("QPS")
    plt.ylabel("50th% latency (ms)")
    plt.legend()
    plt.show()
    # plot the max latency
    plt.show()
    plt.subplot(4,1,2)
    legend=[]
    for exp in lat_c.keys():
        exp_lat = lat_c[exp]
        l = plt.plot(exp_lat["row_key"], exp_lat["row"]['client_max'], 'o-', label=exp)
    legend.append(l)
    plt.xlabel("QPS")
    plt.ylabel("Max latency (ms)")
    plt.legend()
    plt.show()
    # plot the utilization
    plt.subplot(2,1,2)
    plt.ylim(0,1)
    legend=[]
    for exp in util_c.keys():
        exp_lat = util_c[exp]
        l = plt.plot(exp_lat["row_key"], exp_lat["row"]['cpu'], 'o-', label=exp)
        legend.append(l)
    plt.xlabel("QPS")
    plt.ylabel("CPU Utilization")
    plt.legend()
    plt.show()