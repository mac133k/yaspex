import pyslurm
import pandas as pd
from prometheus_client.core import GaugeMetricFamily


class PartitionInfoCollector(object):
	# Job properties of interest
	props = ['name', 'total_nodes', 'total_cpus', 'state']
	# Metric labels
	labels = ['cluster', 'name']
	
	def collect(self):
		# Metric declarations
		PART_NODES = GaugeMetricFamily('partitions_total_nodes', 'Total numbers of nodes per partition grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		PART_CPUS = GaugeMetricFamily('partitions_total_cpus', 'Total numbers of CPUs per partition grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		PART_STATE = GaugeMetricFamily('partitions_state', 'Partition states grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		
		# Load part info from Slurm
		df = pd.DataFrame().from_dict(pyslurm.partition().get(), orient='index').loc[:, self.props]
		df['cluster'] = pyslurm.config().get()['cluster_name']
		# Update the metrics
		df.apply(lambda row: [
				PART_NODES.add_metric(row[self.labels], row['total_nodes']),
				PART_CPUS.add_metric(row[self.labels], row['total_cpus']),
				PART_STATE.add_metric(row[self.labels], int(row['state'] == 'UP')),
			], axis=1, raw=True
		)
		yield PART_NODES
		yield PART_CPUS
		yield PART_STATE
