import logging

from Collectors.AbstractCollector import AbstractCollector


class EnvironmentCollector(AbstractCollector):
    def register_collector(self):
        pass

    async def start(self):
        logging.info(f"Starting {self.__class__}")

    async def stop(self):
        pass
