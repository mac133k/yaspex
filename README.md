# yaspex
Yet Another Slurm-to-Prometheus EXporter

## How is it different from others?

It is written in Python and it uses pyslurm to communicate with the Slurm cluster, so it should be easy to install and set up for Slurm users. It also has a rich collection of metrics.

## Metrics

YASPEx provides the following metrics:

```
  name                        type                                    help
---------------------------------------------------------------------------------------------------------------------------------------------------
slurm_jobs_cpus_alloc         gauge    Numbers of CPUs allocated for jobs in the cluster grouped by cluster, partition, user, name, state
slurm_jobs_cpus_req           gauge    Numbers of CPUs requested for jobs in the cluster grouped by cluster, partition, user, name, state
slurm_jobs_mem_alloc_bytes    gauge  Amounts of memory allocated for jobs in the cluster grouped by cluster, partition, user, name, state
slurm_jobs_mem_req_bytes      gauge  Amounts of memory requested for jobs in the cluster grouped by cluster, partition, user, name, state
slurm_jobs_nodes_alloc        gauge   Numbers of nodes allocated for jobs in the cluster grouped by cluster, partition, user, name, state
slurm_jobs_nodes_req          gauge   Numbers of nodes requested for jobs in the cluster grouped by cluster, partition, user, name, state
slurm_jobs_num                gauge                       Numbers of jobs in the cluster grouped by cluster, partition, user, name, state
slurm_nodes_cpu_load          gauge                           CPU loads on nodes in the cluster grouped by cluster, partition, name, arch
slurm_nodes_cpus              gauge                     Numbers of CPUs on nodes in the cluster grouped by cluster, partition, name, arch
slurm_nodes_cpus_alloc        gauge           Numbers of CPUs allocated on nodes in the cluster grouped by cluster, partition, name, arch
slurm_nodes_mem_alloc_bytes   gauge         Amounts of memory allocated on nodes in the cluster grouped by cluster, partition, name, arch
slurm_nodes_mem_free_bytes    gauge    Amounts of free memory allocated on nodes in the cluster grouped by cluster, partition, name, arch
slurm_nodes_mem_total_bytes   gauge   Total amounts of memory available on nodes in the cluster grouped by cluster, partition, name, arch
slurm_partitions_state        gauge                                                             Partition states grouped by cluster, name
slurm_partitions_total_cpus   gauge                                          Total numbers of CPUs per partition grouped by cluster, name
slurm_partitions_total_nodes  gauge                                         Total numbers of nodes per partition grouped by cluster, name
```

The labels used for each metric are mentioned in the help section after `grouped by`. Some labels can be included or ignored depends on the settings in `conf/env.sh` described in the configuration section below. Job resource requirements and allocations are extracted from the respective TRES strings.

## How does it work?

One instance of YASPEx can monitor only one Slurm cluster. It does not need to run on a cluster node, but must be able to communicate with Slurm master, so Munge keys and Slurm conf must be locally available.

YASPEx gets the job, partition and node data from Slurm using PySlurm, generates metrics and saves the results in the Prometheus client's registry.

## Installation

### Pre-requisites

The host where YASPEx is installed must be able to connect to the monitored Slurm cluster:
* [Munge](https://github.com/dun/munge/wiki/Installation-Guide) must be installed and deamon must be running
* [Slurm](https://github.com/SchedMD/slurm) configuration and libraries must be installed, but the daemon does not need to be running locally
* [PySLURM](https://pyslurm.github.io/) must be installed matching the version of Slurm

Make sure to use Python v3+ and install the following modules:

```
pip install prometheus_client gunicorn flask
```

### Configuration

Clone the repo or download the zipped archive and unpack to `yaspex` dir. Create the local environment configuration from the template:

```
cd yaspex
cp conf/env.sh.template conf/env.sh
```

Edit `conf/env.sh` and make sure the `SLURM_HOME` path is set correctly. Extra settings for fine-tuning or debugging can be passed to gunicorn as a command line options string in the GUNICORN_OPTS variable.

#### Metric settings

There are settings to include or ignore specific labels, or null/zero values which all are set to `ignore` by default:

```
export METRIC_LABEL_JOB_ID=ignore
export METRIC_LABEL_USER_ID=ignore
export METRIC_LABEL_NODE_NAME=ignore
export METRIC_LABEL_NODE_ARCH=ignore
export METRIC_VALUE_NULL=ignore
```

Ingoring a label affects the metric aggregation and decreases the canrdinality which means there is less lines to collect from the `/metrics` endpoint. These settings should be optimized according to the size of the cluster and the throughput, and the desired level of details of the metric data for further analysis or visualisation. 

Similarly ignoring all metrics with zero values reduces the size of the `/metrics` output and in effect the size of the storage in TSDB. Note however that some labels may be missing from the data set, ie. if there nodes or partitions in the cluster that are not used and have all metrics at 0, the metrics with the corresponding labels will not be recorded and will not be available in the TSDB.

## Starting and stopping

Start the web app using the `start.sh` script. Visit `$GUNICORN_HOST:$GUNICORN_PORT/metrics` to see if it is working. The file with gunicorn's process ID is saved in `yaspex/var/pid`, stdout and stderr are redirected to the log file in `yaspex/var/log/messages.log`.

Stop the web app using the `stop.sh` script.

## Prometheus integration

In `prometheus.yml` under the `scrape_configs` section add the following:

```
  - job_name: 'slurm'
    static_configs:
    - targets: ['localhost:10080']
```

Then reload the configuration and check the graph console for the new metrics.

Note: Check the target status to see how much time does it take for Prometheus to collect the metrics and how does it relate to the monitoring interval. The interval may need to be adjusted depending on the cluster size, ie. numbers of nodes or jobs running/pending, which then determines the size of metrics data.

### PromQL examples

All metric names and labels are listed at the top of this document. The names start with the `slurm_` prefix, so are easy to locate in the dropdowm in Prometheus graph console.

To get the number of jobs running in the cluster type:

```sum(slurm_jobs_num{state='RUNNING'})```

To get the number of CPUs allocated to running jobs vs. the total number of CPUs available in the cluster type:

```sum(slurm_jobs_cpus_alloc{state='RUNNING'})```

To the the number of all CPUs available in the cluster type:

```sum(slurm_partitions_cpus_total)```

To compare the numbers of CPUs allocated vs. CPUs total the last two queries can be plotted on 2 graphs in Prometheus or on a single one in another graphing software, ie. Grafana.
