from abc import abstractmethod, ABCMeta


class AbstractCollector(metaclass=ABCMeta):
    def __init__(self, writer):
        self.db_writer = writer

    @abstractmethod
    def register_collector(self):
        pass

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass
