from abc import ABC, abstractmethod

from flask import Blueprint

from dailys_web.data_source import DataSource


class BaseBlueprint(ABC):

    def __init__(self, data_source: DataSource, path: str):
        self.data_source = data_source
        self.blueprint = Blueprint(path, __name__, template_folder='templates')

    @abstractmethod
    def register(self):
        pass
