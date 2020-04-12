from abc import ABC, abstractmethod


class View(ABC):

    def __init__(self, data_source):
        self.data_source = data_source

    @abstractmethod
    def get_path(self):
        pass

    @abstractmethod
    def call(self, **kwargs):
        pass
