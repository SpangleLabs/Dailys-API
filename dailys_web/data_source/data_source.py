from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Union, Set

max_date = datetime(9999, 12, 30, 12, 0, 0)

DailysData = Dict[str, Any]  # Just the "data" part of a DailysEntry
DailysEntry = Dict[str, Any]  # A full dailys entry, with data, source, stat name, and date
DailysEntries = List[DailysEntry]  # A list of dailys entries
DailysDate = Union[datetime, str]  # A date, can be a datetime object, or "earliest", "latest", "static"
#
#
# class DailysEntry(TypedDict):
#     stat_name: str
#     source: str
#     date: str
#     data: DailysData


class CantUpdate(Exception):
    pass


class DataSource(ABC):

    @abstractmethod
    def get_unique_stat_names(self) -> Set[str]:
        pass

    @abstractmethod
    def get_entries_for_stat(self, stat_name: str) -> DailysEntries:
        pass

    @abstractmethod
    def remove_stat_on_date(self, stat_name: str, view_date: DailysDate) -> None:
        pass

    @abstractmethod
    def get_entries_for_stat_on_date(self, stat_name: str, view_date: DailysDate) -> DailysEntries:
        pass

    @abstractmethod
    def get_entries_over_range(self, start_date: DailysDate, end_date: DailysDate) -> DailysEntries:
        pass

    @abstractmethod
    def get_entries_for_stat_over_range(
            self,
            stat_name: str,
            start_date: DailysDate,
            end_date: DailysDate
    ) -> DailysEntries:
        pass

    @abstractmethod
    def update_entry_for_stat_on_date(
            self,
            stat_name: str,
            update_date: DailysDate,
            new_data: DailysData,
            source: str) -> DailysEntry:
        pass

    @abstractmethod
    def get_latest_n_entries_for_stat(self, stat_name: str, n: int) -> List[DailysData]:
        pass
