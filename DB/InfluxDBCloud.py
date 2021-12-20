import logging

import certifi
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import ASYNCHRONOUS

from DB.AbstractDB import AbstractDB


class InfluxDBCloud(AbstractDB):
    def __init__(self, url, bucket, token, org):
        self._write_api = None
        self.url = url
        self.bucket = bucket
        self.token = token
        self.org = org

    def __enter__(self):
        self._client = InfluxDBClient(url=self.url,
                                      token=self.token,
                                      org=self.org,
                                      ssl_ca_cert=certifi.where())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._write_api:
            self._write_api.close()
        self._client.close()

    def write(self, datapoint):
        if not self._write_api:
            self._write_api = self._client.write_api(write_options=ASYNCHRONOUS)
        self._write_api.write(self.bucket, self.org, datapoint)
        logging.debug(f"Wrote {datapoint} to {self.bucket}")
