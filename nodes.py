import os
import pyslurm
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
		nodes = pyslurm.node().get()
		cluster = pyslurm.config().get()['cluster_name']
		for node in nodes.keys():
			labels_ = [node[l] for l in self.labels]
			for partition in node['partitions']:
				labels_ = [cluster, partition] + labels_
				if 'METRIC_VALUE_NULL' in os.environ and os.environ['METRIC_VALUE_NULL'].lower() == 'include':
					NODES_CPUS.add_metric(labels, node['cpus'])
					NODES_CPUS_ALLOC.add_metric(labels, node['alloc_cpus'])
					NODES_CPU_LOAD.add_metric(labels, node['cpu_load']/100.0)
					NODES_MEM_TOTAL.add_metric(labels, node['real_memory')*1000**2) # MB to Bytes
					NODES_MEM_ALLOC.add_metric(labels, node['alloc_mem')*1000**2)   # MB to Bytes
					NODES_MEM_FREE.add_metric(labels,  node['free_mem']*2**20)      # MiB to Bytes
				else:
					NODES_CPUS.add_metric(labels, node['cpus'])			if node['cpus'] > 0 else None
					NODES_CPUS_ALLOC.add_metric(labels, node['alloc_cpus'])		if node['alloc_cpus'] > 0 else None
					NODES_CPU_LOAD.add_metric(labels, node['cpu_load']/100.0) 	if node['cpu_load'] > 0 else None
					NODES_MEM_TOTAL.add_metric(labels, node['real_memory']*1000**2)	if node['real_memory'] > 0 else None
					NODES_MEM_ALLOC.add_metric(labels, node['alloc_mem']*1000**2)	if node['alloc_mem'] > 0 else None
					NODES_MEM_FREE.add_metric(labels,  node['free_mem']*2**20)	if node['free_mem'] > 0 else None
		yield NODES_CPUS
		yield NODES_CPUS_ALLOC
		yield NODES_CPU_LOAD
		yield NODES_MEM_TOTAL
		yield NODES_MEM_FREE
		yield NODES_MEM_ALLOC

