from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Union

import firebase_admin
from firebase_admin import firestore
from google.cloud.firestore_v1 import Query
from google.cloud.firestore_v1.document import DocumentReference


max_date = datetime(9999, 12, 30, 12, 0, 0)

DailysData = Dict[str, Any]
DailysEntry = Dict[str, Any]
DailysEntries = List[DailysEntry]
DailysDate = Union[datetime, str]


class CantUpdate(Exception):
    pass


class DataSource:

    def __init__(self):
        firebase_admin.initialize_app()
        self.data_source = firestore.client().collection('Dailys stats')

    def get_stat_data(self, stat_name: str) -> DailysEntries:
        return [
            x.to_dict()
            for x
            in self.data_source.where("stat_name", "==", stat_name).order_by("date").get()
        ]

    def _get_stat_for_date(self, stat_name: str, view_date: DailysDate) -> List[DocumentReference]:
        data_partial = self.data_source.where("stat_name", "==", stat_name)
        if view_date == "latest":
            data_partial = data_partial\
                .where("date", "<=", max_date)\
                .order_by("date", direction=Query.DESCENDING)\
                .limit(1)
        elif view_date == "static":
            data_partial = data_partial.where("date", "==", "static")
        else:
            start_datetime = datetime.combine(view_date, time(0, 0, 0))
            end_datetime = datetime.combine(view_date + timedelta(days=1), time(0, 0, 0))
            data_partial = data_partial.where("date", ">=", start_datetime).where("date", "<", end_datetime)
        return list(data_partial.get())

    def get_stat_for_date(self, stat_name: str, view_date: DailysDate) -> DailysEntries:
        return [x.to_dict() for x in self._get_stat_for_date(stat_name, view_date)]

    def get_all_stats_over_range(self, start_date: DailysDate, end_date: DailysDate) -> DailysEntries:
        data_partial = self.data_source
        # Filter start date
        if start_date != "earliest":
            start_datetime = datetime.combine(start_date, time(0, 0, 0))
            data_partial = data_partial.where("date", ">=", start_datetime)
        # Filter end date
        if end_date != "latest":
            end_datetime = datetime.combine(end_date + timedelta(days=1), time(0, 0, 0))
            data_partial = data_partial.where("date", "<=", end_datetime)
        # Collapse data to dicts
        stat_list = [x.to_dict() for x in data_partial.order_by("date").get()]
        # If date range is unbounded, filter out static data
        if start_date == "earliest" and end_date == "latest":
            stat_list = [x for x in stat_list if x['date'] != 'static']
        return stat_list

    def get_stat_over_range(self, stat_name: str, start_date: DailysDate, end_date: DailysDate) -> DailysEntries:
        data_partial = self.data_source.where("stat_name", "==", stat_name)
        # Filter start date
        if start_date != "earliest":
            start_datetime = datetime.combine(start_date, time(0, 0, 0))
            data_partial = data_partial.where("date", ">=", start_datetime)
        # Filter end date
        if end_date != "latest":
            end_datetime = datetime.combine(end_date + timedelta(days=1), time(0, 0, 0))
            data_partial = data_partial.where("date", "<=", end_datetime)
        # Collapse data to dicts
        data = [x.to_dict() for x in data_partial.order_by("date").get()]
        # If date range is unbounded, filter out static data
        if start_date == "earliest" and end_date == "latest":
            data = [x for x in data if x['date'] != 'static']
        return data

    def set_stat_on_date(
            self,
            stat_name: str,
            update_date: DailysDate,
            new_data: DailysDatum,
            source: str) -> DailysEntry:
        # Construct new data object
        total_data = {'stat_name': stat_name}
        if update_date == "latest":
            raise CantUpdate("Can't update data on latest")
        elif update_date == "static":
            total_data['date'] = "static"
        else:
            total_data['date'] = datetime.combine(update_date, time(0, 0, 0))
        total_data['source'] = source or "Unknown [via API]"
        total_data['data'] = new_data
        # See if data exists
        data = self._get_stat_for_date(stat_name, update_date)
        if len(data) == 1:
            self.data_source.document(data[0].id).set(total_data)
        else:
            self.data_source.add(total_data)
        return total_data

    def get_stat_latest_n(self, stat_name: str, n: int) -> List[DailysData]:
        raw_data = self.data_source.where("stat_name", "==", stat_name)\
            .where("date", "<", max_date)\
            .order_by("date", direction=Query.DESCENDING).limit(n).get()
        sleeps = [x.to_dict()['data'] for x in raw_data]
        return sleeps
