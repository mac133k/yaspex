import pyslurm
from prometheus_client.core import GaugeMetricFamily


class PartitionInfoCollector(object):
	# Job properties of interest
	props = ['name', 'total_nodes', 'total_cpus', 'state']
	# Metric labels
	labels = ['cluster', 'name']
	
	def collect(self):
		# Metric declarations
		PART_NODES = GaugeMetricFamily('slurm_partitions_total_nodes', 'Total numbers of nodes per partition grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		PART_CPUS = GaugeMetricFamily('slurm_partitions_total_cpus', 'Total numbers of CPUs per partition grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		PART_STATE = GaugeMetricFamily('slurm_partitions_state', 'Partition states grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		
		# Load part info from Slurm
		cluster = pyslurm.config().get()['cluster_name']
		partitions = pyslurm.partition().get()
		# Update the metrics
		for partition in partitions.keys():
			PART_NODES.add_metric([cluster, partition], partitions[partition]['total_nodes'])
			PART_CPUS.add_metric( [cluster, partition], partitions[partition]['total_cpus'])
			PART_STATE.add_metric([cluster, partition], int(partitions[partition]['state'] == 'UP'))
		yield PART_NODES
		yield PART_CPUS
		yield PART_STATE
