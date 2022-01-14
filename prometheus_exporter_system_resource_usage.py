#!/usr/bin/env python.5

from prometheus_client import start_http_server, Counter
import time
import psutil

UPDATE_PERIOD = 300
SYSTEM_USAGE = prometheus_client.Gauge('system_usage',
                                       'Hold current system resource usage',
                                       ['resource_type'])

if __name__ == '__main__':
  prometheus_client.start_http_server(9999)
  
while True:
  SYSTEM_USAGE.labels('CPU').set(psutil.cpu_percent())
  SYSTEM_USAGE.labels('Memory').set(psutil.virtual_memory()[2])
  time.sleep(UPDATE_PERIOD)
