from abc import ABC, abstractmethod

from dailys_web.data_source import DataSource


class View(ABC):

    def __init__(self, data_source: DataSource):
        self.data_source = data_source

    @abstractmethod
    def get_path(self):
        pass

    @abstractmethod
    def call(self, **kwargs):
        pass
