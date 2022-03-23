#!/usr/local/bin/python3.10

import os
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

token = "txKsBZJffvSDBSv-QM1Z4R0CWDYhCp4O-EYJHtlWERR1KtWtuKdX6xu3jXzYgr2Pe_z0Z3BW_wvTChLXBO2jrQ=="
org = "ALE"
bucket = "ALE"

client = InfluxDBClient(url="http://localhost:8086", token=token, org=org)

write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()
