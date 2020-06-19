import os
import pyslurm
import pandas as pd
from prometheus_client.core import GaugeMetricFamily


class NodeInfoCollector(object):
	# Node properties of interest
	props = ['partitions', 'cpus', 'cpu_load', 'free_mem', 'real_memory', 'alloc_cpus', 'alloc_mem']
	# Metric labels
	labels = ['cluster', 'partition']
	if 'METRIC_LABEL_NODE_NAME' in os.environ and os.environ['METRIC_LABEL_NODE_NAME'].lower() == 'include':
		props.append('name')
		labels.append('name')
	if 'METRIC_LABEL_NODE_ARCH' in os.environ and os.environ['METRIC_LABEL_NODE_ARCH'].lower() == 'include':
		props.append('arch')
		labels.append('arch')
	
	def collect(self):
		# Metric declarations
		NODES_CPUS = GaugeMetricFamily('slurm_nodes_cpus', 'Numbers of CPUs on nodes in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		NODES_CPUS_ALLOC = GaugeMetricFamily('slurm_nodes_cpus_alloc', 'Numbers of CPUs allocated on nodes in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		NODES_CPU_LOAD = GaugeMetricFamily('slurm_nodes_cpu_load', 'CPU loads on nodes in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		NODES_MEM_TOTAL = GaugeMetricFamily('slurm_nodes_mem_total', 'Total amounts of memory available on nodes in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels, unit='bytes')
		NODES_MEM_FREE = GaugeMetricFamily('slurm_nodes_mem_free', 'Amounts of free memory allocated on nodes in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels, unit='bytes')
		NODES_MEM_ALLOC = GaugeMetricFamily('slurm_nodes_mem_alloc', 'Amounts of memory allocated on nodes in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels, unit='bytes')
		
		# Load node info from Slurm
		df = pd.DataFrame().from_dict(pyslurm.node().get(), orient='index').loc[:, self.props]
		# Tidy up the columns
		df = df.explode('partitions')
		df.rename(columns={
				'partitions':	'partition',
				'free_mem':	'mem_free',
				'real_memory':	'mem_total',
				'alloc_mem':	'mem_alloc',
				'alloc_cpus':	'cpus_alloc'
			}, inplace=True
		)
		df.loc[:, self.labels[1:]] = df.loc[:, self.labels[1:]].fillna('NA')
		df = df.fillna(0.0)
		if len(self.labels) < 3:
			df = df.groupby(self.labels[1:]).sum().reset_index()
		df['cluster'] = pyslurm.config().get()['cluster_name']
		df['cpu_load'] /= 100.0
		df.loc[:, ['mem_total', 'mem_alloc']] *= 1000**2 # MB to Bytes
		df['mem_free'] *= 2**20 # MiB to Bytes
		# Update the metrics
		if 'METRIC_VALUE_NULL' in os.environ and os.environ['METRIC_VALUE_NULL'].lower() == 'include':
			df.apply(lambda row: [
					NODES_CPUS.add_metric(row[self.labels], row['cpus']),	
					NODES_CPUS_ALLOC.add_metric(row[self.labels], row['cpus_alloc']),	
					NODES_CPU_LOAD.add_metric(row[self.labels], row['cpu_load']),	
					NODES_MEM_TOTAL.add_metric(row[self.labels], row['mem_total']),	
					NODES_MEM_FREE.add_metric(row[self.labels], row['mem_free']),	
					NODES_MEM_ALLOC.add_metric(row[self.labels], row['mem_alloc']),	
				], axis=1, raw=True
			)
		else:
			int_cols = ['mem_total', 'mem_free', 'mem_alloc', 'cpus', 'cpus_alloc']
			df.loc[:, int_cols] = df.loc[:, int_cols].astype(int)
			df.apply(lambda row: [
					NODES_CPUS.add_metric(row[self.labels], row['cpus']) if row['cpus'] > 0 else None,	
					NODES_CPUS_ALLOC.add_metric(row[self.labels], row['cpus_alloc']) if row['cpus_alloc'] > 0 else None,	
					NODES_CPU_LOAD.add_metric(row[self.labels], row['cpu_load']) if row['cpu_load'] > 0 else None,	
					NODES_MEM_TOTAL.add_metric(row[self.labels], row['mem_total']) if row['mem_total'] > 0 else None,	
					NODES_MEM_FREE.add_metric(row[self.labels], row['mem_free']) if row['mem_free'] > 0 else None,	
					NODES_MEM_ALLOC.add_metric(row[self.labels], row['mem_alloc']) if row['mem_alloc'] > 0 else None,	
				], axis=1, raw=True
			)
		yield NODES_CPUS
		yield NODES_CPUS_ALLOC
		yield NODES_CPU_LOAD
		yield NODES_MEM_TOTAL
		yield NODES_MEM_FREE
		yield NODES_MEM_ALLOC

