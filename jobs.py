import pwd
import pyslurm
import pandas as pd
from prometheus_client.core import GaugeMetricFamily


class JobInfoCollector(object):
	# Job properties of interest
	job_props = ['partition', 'name', 'job_state', 'user_id', 'tres_req_str', 'tres_alloc_str']
	# Metric labels
	labels = ['cluster', 'partition', 'user', 'name', 'state']
	
	def collect(self):
		JOBS_NUM = GaugeMetricFamily('jobs_num', 'Numbers of jobs in the cluster grouped by {}'.format(', '.join(self.labels)), labels=self.labels)
		jobs = pyslurm.job().get()
		jobdf = pd.DataFrame().from_dict(jobs, orient='index').loc[:, self.job_props]
		# Translate user IDs to names
		jobdf['user'] = jobdf.user_id.apply(lambda uid: pwd.getpwuid(uid).pw_name)
		# Extract TRES req
		jobdf['cpu_req'] = jobdf.tres_req_str.str.extract(r'cpu=(?P<cpu_req>[0-9]+)').fillna(0).astype(int) 
		jobdf['mem_req'] = jobdf.tres_req_str.str.extract(r'mem=(?P<mem_req>[0-9]+)').fillna(0).astype(int) 
		jobdf['node_req'] = jobdf.tres_req_str.str.extract(r'node=(?P<node_req>[0-9]+)').fillna(0).astype(int) 
		# Extract TRES alloc
		jobdf['cpu_alloc'] = jobdf.tres_alloc_str.str.extract(r'cpu=(?P<cpu_alloc>[0-9]+)').fillna(0).astype(int) 
		jobdf['mem_alloc'] = jobdf.tres_alloc_str.str.extract(r'mem=(?P<mem_alloc>[0-9]+)').fillna(0).astype(int) 
		jobdf['node_alloc'] = jobdf.tres_alloc_str.str.extract(r'node=(?P<node_alloc>[0-9]+)').fillna(0).astype(int) 
		# Tidy up the columns
		jobdf.drop(columns=['user_id', 'tres_req_str', 'tres_alloc_str'], inplace=True)
		jobdf.rename(columns={'job_state': 'state'}, inplace=True)
		# Aggregate rows
		job_num = jobdf.groupby(self.labels[1:]).count().iloc[:,-1].values
		jobdf = jobdf.groupby(self.labels[1:]).sum().reset_index()
		jobdf['job_num'] = job_num
		jobdf['cluster'] = pyslurm.config().get()['cluster_name']
		# Update the metrics
		jobdf.apply(lambda row: JOBS_NUM.add_metric(row[self.labels], row['job_num']), axis=1, raw=True)
		yield JOBS_NUM

