# yaspex
Yet Another Slurm-to-Prometheus EXporter

## How is it different from others?

It is written in Python and it uses pyslurm to communicate with the Slurm cluster, so it should be easy to install and set up for Slurm users. It also has a rich collection of metrics:
* jobs: 
  * metrics: number, CPU req/alloc, memory req/alloc, nodes req/alloc
  * labels: cluster, partition, user, name, state
* nodes:
  * metrics: CPUs total/alloc, CPU load, memory total/free/alloc
  * labels: cluster, partition, name, arch
* partitions:
  * metrics: total numbers of nodes and CPUs, state (UP = 1, otherwise = 0)

Job resource requirements and allocations are extracted from the respective TRES strings.

## How does it work?

One instance of YASPEx can monitor only one Slurm cluster. It does not need to run on a cluster node, but must be able to communicate with Slurm master, so Munge keys and Slurm conf must be locally available.

YASPEx gets the job, partition and node data from Slurm using PySlurm, converts the dictionaries to Pandas dataframes, performs data clean-ups and aggregations, then saves the results in the Prometheus client's metrics registry.

## Installation

### Pre-requisites

The host where YASPEx is installed must be able to connect to the monitored Slurm cluster:
* [Munge](https://github.com/dun/munge/wiki/Installation-Guide) must be installed and deamon must be running
* [Slurm](https://github.com/SchedMD/slurm) configuration and libraries must be installed, but the daemon does not need to be running locally
* [PySLURM](https://pyslurm.github.io/) must be installed matching the version of Slurm

Make sure to use Python v3+ and install the following modules:

```
pip install pandas prometheus_client gunicorn flask
```

### Configuration

Clone the repo or download the zipped archive and unpack to `yaspex` dir. Create the local environment configuration from the template:

```
cd yaspex
cp conf/env.sh.template conf/env.sh
```

Edit `conf/env.sh` and make sure the `SLURM_HOME` path is set correctly. Extra settings for fine-tuning or debugging can be passed to gunicorn as a command line options string in the GUNICORN_OPTS variable.

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
