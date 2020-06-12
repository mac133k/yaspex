import pyslurm
import pandas as pd
from prometheus_client.core import GaugeMetricFamily


class NodeInfoCollector(object):
	# Node properties of interest
	node_props = ['name', 'partitions', 'arch', 'cpus', 'cpu_load', 'free_mem', 'real_memory', 'alloc_cpus', 'alloc_mem']
	# Metric labels
	labels = ['cluster', 'partition', 'name', 'arch']
	
	def collect(self):
		# Metric declarations
		NODES_CPUS = GaugeMetricFamily('nodes_cpus', 'Numbers of CPUs on nodes in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		NODES_CPUS_ALLOC = GaugeMetricFamily('nodes_cpus_alloc', 'Numbers of CPUs allocated on nodes in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		NODES_CPU_LOAD = GaugeMetricFamily('nodes_cpu_load', 'CPU loads on nodes in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		NODES_MEM_TOTAL = GaugeMetricFamily('nodes_mem_total', 'Total amounts of memory available on nodes in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels, unit='bytes')
		NODES_MEM_FREE = GaugeMetricFamily('nodes_mem_free', 'Amounts of free memory allocated on nodes in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels, unit='bytes')
		NODES_MEM_ALLOC = GaugeMetricFamily('nodes_mem_alloc', 'Amounts of memory allocated on nodes in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels, unit='bytes')
		
		# Load node info from Slurm
		nodes = pyslurm.node().get()
		nodedf = pd.DataFrame().from_dict(nodes, orient='index').loc[:, self.node_props]
		nodedf['cluster'] = pyslurm.config().get()['cluster_name']
		# Tidy up the columns
		nodedf = nodedf.explode('partitions')
		nodedf.rename(columns={
				'partitions':	'partition',
				'free_mem':	'mem_free',
				'real_memory':	'mem_total',
				'alloc_mem':	'mem_alloc',
				'alloc_cpus':	'cpus_alloc'
			}, inplace=True
		)
		nodedf.loc[:, self.labels] = nodedf.loc[:, self.labels].fillna('NA')
		nodedf = nodedf.fillna(0.0)
		nodedf['cpu_load'] /= 100.0
		nodedf.loc[:, ['mem_total', 'mem_alloc']] *= 1000**2 # MB to Bytes
		nodedf['mem_free'] *= 2**20 # MiB to Bytes
		# Update the metrics
		nodedf.apply(lambda row: [
				NODES_CPUS.add_metric(row[self.labels], row['cpus']),	
				NODES_CPUS_ALLOC.add_metric(row[self.labels], row['cpus_alloc']),	
				NODES_CPU_LOAD.add_metric(row[self.labels], row['cpu_load']),	
				NODES_MEM_TOTAL.add_metric(row[self.labels], row['mem_total']),	
				NODES_MEM_FREE.add_metric(row[self.labels], row['mem_free']),	
				NODES_MEM_ALLOC.add_metric(row[self.labels], row['mem_alloc']),	
			], axis=1, raw=True
		)
		yield NODES_CPUS
		yield NODES_CPUS_ALLOC
		yield NODES_CPU_LOAD
		yield NODES_MEM_TOTAL
		yield NODES_MEM_FREE
		yield NODES_MEM_ALLOC

