import asyncio
import logging
import os
import threading
from time import sleep
from unittest.mock import MagicMock

from dotenv import load_dotenv

from Collectors.EdgeOS.Collector import EdgeOSCollector
from DB.InfluxDBCloud import InfluxDBCloud

_loop = None


def schedule_background(coro):
    global _loop
    if _loop is None:
        _loop = asyncio.new_event_loop()
        threading.Thread(target=_loop.run_forever, daemon=True).start()
    _loop.call_soon_threadsafe(asyncio.create_task, coro)


if __name__ == '__main__':
    load_dotenv("../settings.env")

    influx_url = os.environ.get('INFLUX_URL')
    influx_token = os.environ.get('INFLUX_TOKEN')
    influx_org = os.environ.get('INFLUX_ORG')
    influx_bucket = os.environ.get('INFLUX_BUCKET')

    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
    logger = logging.getLogger()

    if os.environ.get("DEBUG_MODE"):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    with InfluxDBCloud(influx_url, influx_bucket, influx_token, influx_org) as db_writer:
        if os.environ.get("NO_DB_WRITE"):
            db_writer.write = MagicMock(side_effect=lambda x: logging.info("Suppressed DB Write"))

        eosc = EdgeOSCollector(db_writer)
        eosc.register_collector()

        schedule_background(eosc.start())

    logging.info("Hit")
    while True:
        sleep(1)
