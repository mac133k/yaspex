import os
from flask import Flask, Response
from prometheus_client import multiprocess, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST, REGISTRY

app = Flask('yaspex')

import jobs
import partitions
import nodes

REGISTRY.register(jobs.JobInfoCollector())
REGISTRY.register(partitions.PartitionInfoCollector())
REGISTRY.register(nodes.NodeInfoCollector())

@app.route('/')
def status():
	return Response('PID: {}\n'.format(os.getpid()))


@app.route('/metrics')
def metrics():
	multiprocess.MultiProcessCollector(REGISTRY)
	return Response(generate_latest(REGISTRY), mimetype=CONTENT_TYPE_LATEST)
