import abc
from abc import ABC


class AbstractDB(ABC):

    @abc.abstractmethod
    def __enter__(self, *args, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        raise NotImplementedError

    @abc.abstractmethod
    def write(self, data):
        raise NotImplementedError
