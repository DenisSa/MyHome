from aioedgeos import EdgeOS, TaskEvery
from aiohttp import ServerFingerprintMismatch
from dotenv import load_dotenv

import asyncio
from contextlib import AsyncExitStack
import logging
import os
import aiohttp
from binascii import a2b_hex, b2a_hex

from Collectors.EdgeOS.Datapoints import Interfaces, LatencyPoint, SystemStats
from DB.InfluxDBCloud import InfluxDBCloud


class EdgeOSCollector:

    @staticmethod
    def process_interfaces(value, hostname):
        if_fields = [
            'rx_packets', 'rx_bytes', 'rx_errors', 'rx_dropped',
            'tx_packets', 'tx_bytes', 'tx_errors', 'tx_dropped',
            'rx_bps', 'tx_bps'
        ]
        for interface, x in value.items():
            datapoint = Interfaces(router=hostname,
                                   ifname=interface,
                                   **dict((field_name, int(x['stats'][field_name])) for field_name in if_fields)
                                   )
            yield datapoint

    async def latency_check(self, local_client, edgeos, hostname, target, count, size):
        try:
            logging.info(f"Pinging {target}")
            await edgeos.ping(target=target, count=count, size=size)

            local_client.write(LatencyPoint(router=hostname,
                                            target=target,
                                            latency=edgeos.sysdata['ping-data'][target].get('avg', '1000'),
                                            lost=edgeos.sysdata['ping-data'][target].get('lost', None)))
            logging.info(f"Pinging {target} and storing data done, sleeping for {self.ping_interval} seconds")
        except:
            logging.exception("latency_check")

    def __init__(self, writer):
        self.db_writer = writer
        self.router_tagname = None
        self.router_ssl = None
        self.ssl_check = None
        self.ping_interval = None
        self.ping_size = None
        self.ping_count = None
        self.ping_target = None
        self.influx_bucket = None
        self.influx_org = None
        self.influx_token = None
        self.influx_url = None
        self.router_username = None
        self.router_password = None
        self.router_url = None
        self.debug_mode = None

    async def main_loop(self):
        async with AsyncExitStack() as stack:
            try:
                ''' ROUTER SETUP '''
                logging.info(f"CONNECTING TO ROUTER {self.router_url} with user {self.router_username}")
                router = await stack.enter_async_context(
                    EdgeOS(self.router_username, self.router_password, self.router_url, ssl=self.ssl_check))
                await router.config()

                hostname = self.router_tagname or router.sysconfig['system']['host-name']

                logging.info(f"CONNECTED TO ROUTER {hostname}")

                '''
                For ping testing, let's breakdown the list into targets and make sure that
                we don't start pinging all of them at once by staggering them based on their
                position in the list
                '''
                targets = self.ping_target.split('/')
                for i, target in enumerate(targets):
                    offset = i * int(self.ping_interval / len(targets))
                    logging.info(f"LAUNCHING LATENCY CHECK LOOP FOR {target} with offset {offset}")
                    await stack.enter_async_context(TaskEvery(self.latency_check,
                                                              self.db_writer,
                                                              router,
                                                              hostname,
                                                              target,
                                                              self.ping_count,
                                                              self.ping_size,
                                                              interval=self.ping_interval,
                                                              offset=offset))

                logging.info("STARTING MAIN WEBSOCKET LOOP")
                async for payload in router.stats(
                        subs=["interfaces", "system-stats"]):
                    for key, value in payload.items():
                        if not isinstance(value, dict):
                            logging.debug(
                                f"{value} for {key} isn't a dict, would likely cause trouble in processing skipping")
                            continue
                        if key == 'system-stats':
                            datapoint = SystemStats(router=hostname,
                                                    cpu=value['cpu'],
                                                    mem=value['mem'],
                                                    uptime=value['uptime'])
                            self.db_writer.write(datapoint)
                        elif key == 'interfaces':
                            self.db_writer.write(EdgeOSCollector.process_interfaces(value, hostname))
            except ServerFingerprintMismatch as e:
                fphash = b2a_hex(e.got).decode()
                print(f'''
    ===============   TLS/SSL HASH MISMATCH ===============
    Server replied with different fingerprint hash of {fphash}, it's likely you didn't setup the 
    ssl for your router.  If this is the case please update your environment with the following.
    
    ROUTER_SSL={fphash}
    ===============   TLS/SSL HASH MISMATCH ===============''')

    def register_collector(self):
        self.debug_mode = os.environ.get('DEBUG_MODE', None)

        '''
        If you want to replace the system hostname with something
        else and don't want to change the router config you can
        change it here
        '''
        self.router_tagname = os.environ.get('ROUTER_TAGNAME', None)

        ''' Credentials to get into the webUI '''
        self.router_username = os.environ['ROUTER_USERNAME']
        self.router_password = os.environ['ROUTER_PASSWORD']
        self.router_url = os.environ['ROUTER_URL']

        ''' 
        TRUE for SSL that will validate or the base64 sha256
        fingerprint for the host
        '''
        self.router_ssl = os.environ.get('ROUTER_SSL', 'f' * 64).lower()  # Default to enforcing ssl

        ''' 
        Latency settings - optional, by default will 
        ping 1.1.1.1 every 120 seconds with 3 pings and record
        the stats.
    
        PING_TARGET can take multiple hosts like 1.1.1.1/8.8.8.8
        and will interleve checks
        '''
        self.ping_target = os.environ.get('PING_TARGET', '1.1.1.1')
        self.ping_count = int(os.environ.get('PING_COUNT', 3))
        self.ping_size = int(os.environ.get('PING_SIZE', 50))
        self.ping_interval = int(os.environ.get('PING_INTERVAL', 120))

        self.ssl_check = True
        if isinstance(self.router_ssl, str) and len(self.router_ssl) == 64:
            # presume this is a fingerprint
            self.ssl_check = aiohttp.Fingerprint(a2b_hex(self.router_ssl))
        elif self.router_ssl in ['no', 'false']:
            self.ssl_check = False
        elif self.router_ssl in ['yes', 'true']:
            self.ssl_check = True
        else:
            raise Exception(f"ROUTER_SSL {self.router_ssl} is invalid")

        logging.basicConfig(format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')
        logger = logging.getLogger()
        if self.debug_mode:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

    def start(self):
        asyncio.run(self.main_loop())

    def stop(self):
        pass


if __name__ == '__main__':
    load_dotenv("../../settings.env")

    influx_url = os.environ['INFLUX_URL']
    influx_token = os.environ['INFLUX_TOKEN']
    influx_org = os.environ.get('INFLUX_ORG')
    influx_bucket = os.environ.get('INFLUX_BUCKET')

    with InfluxDBCloud(influx_url, influx_bucket, influx_token, influx_org) as db_writer:
        eosc = EdgeOSCollector(db_writer)
        eosc.register_collector()
        eosc.start()
