import os
import pwd
import pyslurm
import pandas as pd
from prometheus_client.core import GaugeMetricFamily


class JobInfoCollector(object):
	# Job properties of interest
	props = ['partition', 'name', 'job_state', 'user_id', 'tres_req_str', 'tres_alloc_str']
	# Metric labels
	labels = ['cluster', 'partition', 'user', 'name', 'state']
	if 'METRIC_LABEL_JOB_ID' in os.environ:
		if os.environ['METRIC_LABEL_JOB_ID'].lower() == 'include':
			props.append('job_id')
			labels.append('id')
	
	def collect(self):
		# Metric declarations
		JOBS_NUM = GaugeMetricFamily('slurm_jobs_num', 'Numbers of jobs in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		JOBS_CPUS_REQ = GaugeMetricFamily('slurm_jobs_cpus_req', 'Numbers of CPUs requested for jobs in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		JOBS_CPUS_ALLOC = GaugeMetricFamily('slurm_jobs_cpus_alloc', 'Numbers of CPUs allocated for jobs in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		JOBS_MEM_REQ = GaugeMetricFamily('slurm_jobs_mem_req', 'Amounts of memory requested for jobs in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels, unit='bytes')
		JOBS_MEM_ALLOC = GaugeMetricFamily('slurm_jobs_mem_alloc', 'Amounts of memory allocated for jobs in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels, unit='bytes')
		JOBS_NODES_REQ = GaugeMetricFamily('slurm_jobs_nodes_req', 'Numbers of nodes requested for jobs in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		JOBS_NODES_ALLOC = GaugeMetricFamily('slurm_jobs_nodes_alloc', 'Numbers of nodes allocated for jobs in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		
		# Load job info from Slurm
		df = pd.DataFrame().from_dict(pyslurm.job().get(), orient='index').loc[:, self.props]
		# Translate user IDs to names
		df['user'] = df.user_id.apply(lambda uid: pwd.getpwuid(uid).pw_name)
		# Extract TRES req
		df['cpus_req'] = df.tres_req_str.str.extract(r'cpu=(?P<cpus_req>[0-9]+)').fillna(0).astype(int) 
		df['mem_req'] = df.tres_req_str.str.extract(r'mem=(?P<mem_req>[0-9]+)').fillna(0).astype(int) 
		df['nodes_req'] = df.tres_req_str.str.extract(r'node=(?P<nodes_req>[0-9]+)').fillna(0).astype(int) 
		# Extract TRES alloc
		df['cpus_alloc'] = df.tres_alloc_str.str.extract(r'cpu=(?P<cpus_alloc>[0-9]+)').fillna(0).astype(int) 
		df['mem_alloc'] = df.tres_alloc_str.str.extract(r'mem=(?P<mem_alloc>[0-9]+)').fillna(0).astype(int) 
		df['nodes_alloc'] = df.tres_alloc_str.str.extract(r'node=(?P<nodes_alloc>[0-9]+)').fillna(0).astype(int) 
		# Tidy up the columns
		df.drop(columns=['user_id', 'tres_req_str', 'tres_alloc_str'], inplace=True)
		df.rename(columns={'job_state': 'state', 'job_id': 'id'}, inplace=True)
		if 'id' in df.columns:
			df['id'] = df.id.astype(str)
		# Aggregate rows
		job_num = df.groupby(self.labels[1:]).count().iloc[:,-1].values
		df = df.groupby(self.labels[1:]).sum().reset_index()
		df.loc[:, ['mem_req', 'mem_alloc']] *= 1000**2 # convert from MegaBytes to Bytes
		df['job_num'] = job_num
		df['cluster'] = pyslurm.config().get()['cluster_name']
		# Update the metrics
		df.apply(lambda row: [
				JOBS_NUM.add_metric(row[self.labels], row['job_num']),
				JOBS_CPUS_REQ.add_metric(row[self.labels], row['cpus_req']),
				JOBS_CPUS_ALLOC.add_metric(row[self.labels], row['cpus_alloc']),	
				JOBS_MEM_REQ.add_metric(row[self.labels], row['mem_req']),
				JOBS_MEM_ALLOC.add_metric(row[self.labels], row['mem_alloc']),	
				JOBS_NODES_REQ.add_metric(row[self.labels], row['nodes_req']),
				JOBS_NODES_ALLOC.add_metric(row[self.labels], row['nodes_alloc']),	
			], axis=1, raw=True
		)
		yield JOBS_NUM
		yield JOBS_CPUS_REQ
		yield JOBS_CPUS_ALLOC
		yield JOBS_MEM_REQ
		yield JOBS_MEM_ALLOC
		yield JOBS_NODES_REQ
		yield JOBS_NODES_ALLOC

