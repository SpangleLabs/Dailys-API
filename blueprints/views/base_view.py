from abc import ABC


class View(ABC):

    def __init__(self, data_source):
        self.data_source = data_source

    def get_path(self):
        pass

    def call(self, **kwargs):
        pass
