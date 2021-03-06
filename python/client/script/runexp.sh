#!/bin/bash

if [[ -z $1 ]]; then
    echo "Please passing the config file (e.g. script/cfsbaseline.sh)"
    exit -1
fi

source $1

if [[ -z $CFSQuota || -z $CFSCpuset || -z $CgroupName ]]; then
    echo "CFSQuota, CFSCpuset or CgroupName is not set."
    exit -1;
fi


if [[ -z $Tag || -z $Iteration || -z $TaskFile || -z $ServerHost || -z $ServerPort ]]; then
   echo "Tag, WarmupQPS, Iteration, TaskFile, ServerHost, or ServerPort is not set"
   exit -1;
fi

if [[ -z $StartQPS || -z $EndQPS || -z $StepQPS ]]; then
    echo "StartQPS, EndQPS, or StepQPS is not set"
    exit -1
fi

# if [[ -z $ResultDir ]]; then    
#     ResultDir=`date +"%d-%m-%Y_%R:%S"`
# fi

# if [[ -d $ResultDir ]]; then
#     echo "The result directory $ResultDir exists already."
# else
#     echo "Create the result directory $ResultDir."
#     mkdir $ResultDir
# fi

echo "Set $CgroupName cpu.cfs_quota_us to $CFSQuota and the cpuset to $CFSCpuset"
ssh td2 "echo $CFSQuota > /sys/fs/cgroup/cpu/$CgroupName/cpu.cfs_quota_us"
ssh td2 "echo $CFSCpuset > /sys/fs/cgroup/cpuset/$CgroupName/cpuset.cpus"
echo Checking CFSQuota: `ssh td2 "cat /sys/fs/cgroup/cpu/$CgroupName/cpu.cfs_quota_us"`
echo Checking CFSCpuset: `ssh td2 cat /sys/fs/cgroup/cpuset/$CgroupName/cpuset.cpus`
if [[ -z $CFSPeriod ]]; then
    echo "Set $CgroupName cpu.fs_period_us to 100000"
    ssh td2 "echo 100000 > /sys/fs/cgroup/cpu/$CgroupName/cpu.cfs_period_us"
    echo Checking CFSPeriod: `ssh td2 "cat /sys/fs/cgroup/cpu/$CgroupName/cpu.cfs_period_us"`
else
    echo "Set $CgroupName cpu.csf_period_us to $CFSPeriod"
    ssh td2 "echo $CFSPeriod > /sys/fs/cgroup/cpu/$CgroupName/cpu.cfs_period_us"
    echo Checking CFSPeriod: `ssh td2 "cat /sys/fs/cgroup/cpu/$CgroupName/cpu.cfs_period_us"`
fi

if [[ ! -z $CFSCPUQuota ]]; then
    echo "Set $CgroupName cpu.cpu_cfs_quota to $CFSCPUQuota"
    ssh td2 "echo $CFSCPUQuota > /sys/fs/cgroup/cpu/$CgroupName/cpu.cfs_cpu_quota"
    echo Checking CFSCPUQuota: `ssh td2 "cat /sys/fs/cgroup/cpu/$CgroupName/cpu.cfs_cpu_quota"`
fi

if [ -n $WarmupQPS ]; then
    echo "Warming up with $WarmupQPS QPS"
    python /home/xyang/code/fastclient/python/client/script/sendTasks.py ${TaskFile} ${ServerHost} ${ServerPort} ${WarmupQPS} 1000000 200000 warmup_${Tag}_${WarmupQPS}_${Iteration} ${Iteration} order
else
    echo "No warmup"
fi

echo "Start the benchmark"
for ((q=$StartQPS;q<=$EndQPS;q+=$StepQPS)); do
    echo "Evaluating $q QPS"
    echo "========================================="
    ssh td2 "cat /proc/stat" > ./ProcStatBegin_${Tag}_${q}_${Iteration}
    ssh td2 "cat /sys/fs/cgroup/cpu/$CgroupName/cpu.stat" > ./Cgroup-${CgroupName}-CPUStatBegin_${Tag}_${q}_${Iteration}
    python /home/xyang/code/fastclient/python/client/script/sendTasks.py ${TaskFile} ${ServerHost} ${ServerPort} ${q} 1000000 200000 ${Tag}_${q}_${Iteration} ${Iteration} order
    ssh td2 "cat /proc/stat" > ./ProcStatEnd_${Tag}_${q}_${Iteration}
    ssh td2 "cat /sys/fs/cgroup/cpu/$CgroupName/cpu.stat" > ./Cgroup-${CgroupName}-CPUStatEnd_${Tag}_${q}_${Iteration}
    echo "Report:"
    python /home/xyang/code/fastclient/python/client/script/parseIter.py ${Tag}_${q}_${Iteration} ${Iteration}
    python /home/xyang/code/fastclient/python/client/script/parsecpu.py ProcStatBegin_${Tag}_${q}_${Iteration} ProcStatEnd_${Tag}_${q}_${Iteration}
done
