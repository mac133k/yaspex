import os
import re
import pwd
import pyslurm
from prometheus_client.core import GaugeMetricFamily


class JobInfoCollector(object):
	# Job properties of interest
	props = ['partition', 'name', 'job_state']
	# Metric labels
	labels = ['cluster', 'partition', 'name', 'state']
	if 'METRIC_LABEL_USER_ID' in os.environ and os.environ['METRIC_LABEL_USER_ID'].lower() == 'include':
		props.append('user_id')
		labels.append('user')
	if 'METRIC_LABEL_JOB_ID' in os.environ and os.environ['METRIC_LABEL_JOB_ID'].lower() == 'include':
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
		jobs = pyslurm.job().get()
		cluster = pyslurm.config().get()['cluster_name']
		# Compile regular expressions
		rgx_cpu  = re.compile(r'cpu=([0-9]+)')
		rgx_mem  = re.compile(r'mem=([0-9]+)')
		rgx_node = re.compile(r'node=([0-9]+)')
		# Update the metrics
		for job_id in jobs.keys():
			labels_ = [cluster]
			for prop in self.props:
				if prop == 'user_id':
					user_ = (str(jobs[job_id]['user_id']))
					try:
						user_ = pwd.getpwuid(user_).pw_name
					except:
						pass
					labels_.append(user_)
				else:
					labels_.append(str(jobs[job_id][prop]))

			JOBS_NUM.add_metric(labels_, 1.0)
			# Extract requirements and allocations
			if 'METRIC_VALUE_NULL' in os.environ and os.environ['METRIC_VALUE_NULL'].lower() == 'include':
				if 'tres_res_str' in jobs[job_id].keys() and jobs[job_id]['tres_res_str']:
					m = rgx_cpu.search(jobs[job_id]['tres_req_str'])
					JOBS_CPUS_REQ.add_metric(labels_, int(m.group(1)) if m else None)
					m = rgx_mem.search(jobs[job_id]['tres_req_str'])
					JOBS_MEM_REQ.add_metric(labels_, int(m.group(1))*1000**2 if m else None)
					m = rgx_node.search(jobs[job_id]['tres_req_str'])
					JOBS_NODES_REQ.add_metric(labels_, int(m.group(1)) if m else None)
				if 'tres_alloc_str' in jobs[job_id].keys() and jobs[job_id]['tres_alloc_str']:
					m = rgx_cpu.search(jobs[job_id]['tres_alloc_str'])
					JOBS_CPUS_ALLOC.add_metric(labels_, int(m.group(1)) if m else None)
					m = rgx_mem.search(jobs[job_id]['tres_alloc_str'])
					JOBS_MEM_ALLOC.add_metric(labels_, int(m.group(1))*1000**2 if m else None)
					m = rgx_node.search(jobs[job_id]['tres_alloc_str'])
					JOBS_NODES_ALLOC.add_metric(labels_, int(m.group(1)) if m else None)
			else:
				if 'tres_res_str' in jobs[job_id].keys() and jobs[job_id]['tres_res_str']:
					m = rgx_cpu.search(jobs[job_id]['tres_req_str'])
					JOBS_CPUS_REQ.add_metric(labels_, int(m.group(1))) if m else None
					m = rgx_mem.search(jobs[job_id]['tres_req_str'])
					JOBS_MEM_REQ.add_metric(labels_, int(m.group(1))*1000**2) if m else None
					m = rgx_node.search(jobs[job_id]['tres_req_str'])
					JOBS_NODES_REQ.add_metric(labels_, int(m.group(1))) if m else None
				if 'tres_alloc_str' in jobs[job_id].keys() and jobs[job_id]['tres_alloc_str']:
					m = rgx_cpu.search(jobs[job_id]['tres_alloc_str'])
					JOBS_CPUS_ALLOC.add_metric(labels_, int(m.group(1))) if m else None
					m = rgx_mem.search(jobs[job_id]['tres_alloc_str'])
					JOBS_MEM_ALLOC.add_metric(labels_, int(m.group(1))*1000**2) if m else None
					m = rgx_node.search(jobs[job_id]['tres_alloc_str'])
					JOBS_NODES_ALLOC.add_metric(labels_, int(m.group(1))) if m else None
		yield JOBS_NUM
		yield JOBS_CPUS_REQ
		yield JOBS_CPUS_ALLOC
		yield JOBS_MEM_REQ
		yield JOBS_MEM_ALLOC
		yield JOBS_NODES_REQ
		yield JOBS_NODES_ALLOC

