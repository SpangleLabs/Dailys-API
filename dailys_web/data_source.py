import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Union, Set

import firebase_admin
import psycopg2
from firebase_admin import firestore
from google.cloud.firestore_v1 import Query
from google.cloud.firestore_v1.document import DocumentSnapshot
from psycopg2.extras import RealDictCursor

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


class FirestoreDataSource(DataSource):

    def __init__(self):
        firebase_admin.initialize_app()
        self.data_source = firestore.client().collection('Dailys stats')

    def get_unique_stat_names(self) -> Set[str]:
        unique_names = set()
        for stat in self.data_source.get():
            if stat.get("stat_name"):
                unique_names.add(stat.get("stat_name"))
        return unique_names

    def get_entries_for_stat(self, stat_name: str) -> DailysEntries:
        return [
            x.to_dict()
            for x
            in self.data_source.where("stat_name", "==", stat_name).order_by("date").get()
        ]

    def remove_stat_on_date(self, stat_name: str, view_date: DailysDate) -> None:
        docs = self._get_documents_for_stat_on_date(stat_name, view_date)
        if len(docs) == 0:
            raise KeyError
        for doc in docs:
            doc.reference.delete()

    def _get_documents_for_stat_on_date(self, stat_name: str, view_date: DailysDate) -> List[DocumentSnapshot]:
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

    def get_entries_for_stat_on_date(self, stat_name: str, view_date: DailysDate) -> DailysEntries:
        return [x.to_dict() for x in self._get_documents_for_stat_on_date(stat_name, view_date)]

    def get_entries_over_range(self, start_date: DailysDate, end_date: DailysDate) -> DailysEntries:
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

    def get_entries_for_stat_over_range(
            self,
            stat_name: str,
            start_date: DailysDate,
            end_date: DailysDate
    ) -> DailysEntries:
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

    def update_entry_for_stat_on_date(
            self,
            stat_name: str,
            update_date: DailysDate,
            new_data: DailysData,
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
        data = self._get_documents_for_stat_on_date(stat_name, update_date)
        if len(data) == 1:
            self.data_source.document(data[0].id).set(total_data)
        else:
            self.data_source.add(total_data)
        return total_data

    def get_latest_n_entries_for_stat(self, stat_name: str, n: int) -> List[DailysData]:
        raw_data = self.data_source.where("stat_name", "==", stat_name)\
            .where("date", "<", max_date)\
            .order_by("date", direction=Query.DESCENDING).limit(n).get()
        sleeps = [x.to_dict()['data'] for x in raw_data]
        return sleeps


def entry_from_row(row: Dict) -> DailysEntry:
    return {
        "stat_name": row["stat_name"],
        "source": row["source"],
        "date": row["stat_date"],
        "data": row["stat_data"]
    }


def entry_from_static_row(row: Dict) -> DailysEntry:
    return {
        "stat_name": row["stat_name"],
        "source": row["source"],
        "date": "static",
        "data": row["stat_data"]
    }


# noinspection SqlNoDataSourceInspection,PyTypeChecker
class PostgresDataSource(DataSource):

    def __init__(self, db_config: Dict) -> None:
        self.conn = psycopg2.connect(
            host=db_config.get("host", "localhost"),
            database=db_config.get("database", "dailys"),
            user=db_config.get("user", "postgres"),
            password=db_config["password"],
            cursor_factory=RealDictCursor
        )

    def get_unique_stat_names(self) -> Set[str]:
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT DISTINCT stat_name FROM ("
                        "SELECT stat_name FROM dailys_data "
                        "UNION ALL "
                        "SELECT stat_name FROM dailys_static"
                    ") a"
                )
                return set(row["stat_name"] for row in cur.fetchall())

    def get_entries_for_stat(self, stat_name: str) -> DailysEntries:
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT stat_name, source, stat_data FROM dailys_static WHERE stat_name = %s", (stat_name,)
                )
                static_rows = [entry_from_static_row(row) for row in cur.fetchall()]
                cur.execute(
                    "SELECT stat_name, stat_date, source, stat_data FROM dailys_data WHERE stat_name = %s",
                    (stat_name,)
                )
                return [entry_from_row(row) for row in cur.fetchall()] + static_rows

    def remove_stat_on_date(self, stat_name: str, view_date: DailysDate) -> None:
        with self.conn:
            with self.conn.cursor() as cur:
                if view_date == "static":
                    cur.execute("DELETE FROM dailys_static WHERE stat_name = %s", (stat_name,))
                else:
                    cur.execute(
                        "DELETE FROM dailys_data WHERE stat_name = %s AND stat_date = %s",
                        (stat_name, view_date)
                    )
                self.conn.commit()

    def get_entries_for_stat_on_date(self, stat_name: str, view_date: DailysDate) -> DailysEntries:
        with self.conn:
            with self.conn.cursor() as cur:
                if view_date == "static":
                    cur.execute(
                        "SELECT stat_name, source, stat_data FROM dailys_static WHERE stat_name = %s", (stat_name,)
                    )
                    return [entry_from_static_row(row) for row in cur.fetchall()]
                cur.execute(
                    "SELECT stat_name, stat_date, source, stat_data FROM dailys_data "
                    "WHERE stat_name = %s AND stat_date = %s",
                    (stat_name, view_date)
                )
                return [entry_from_row(row) for row in cur.fetchall()]

    def get_entries_over_range(self, start_date: DailysDate, end_date: DailysDate) -> DailysEntries:
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT stat_name, stat_date, source, stat_data FROM dailys_data "
                    "WHERE stat_date >= %s AND stat_date <= %s",
                    (start_date, end_date)
                )
                return [entry_from_row(row) for row in cur.fetchall()]

    def get_entries_for_stat_over_range(
            self,
            stat_name: str,
            start_date: DailysDate,
            end_date: DailysDate
    ) -> DailysEntries:
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT stat_name, stat_date, source, stat_data FROM dailys_data "
                    "WHERE stat_name = %s AND stat_date >= %s AND stat_date <= %s",
                    (stat_name, start_date, end_date)
                )
                return [entry_from_row(row) for row in cur.fetchall()]

    def update_entry_for_stat_on_date(
            self,
            stat_name: str,
            update_date: DailysDate,
            new_data: DailysData,
            source: str
    ) -> DailysEntry:
        with self.conn:
            with self.conn.cursor() as cur:
                if update_date == "static":
                    cur.execute(
                        "INSERT INTO dailys_static (stat_name, source, stat_data) VALUES (%s, %s, %s) "
                        "ON CONFLICT (stat_name) DO UPDATE SET source=excluded.source, stat_data=excluded.stat_data",
                        (stat_name, source, json.dumps(new_data))
                    )
                    self.conn.commit()
                    return
                cur.execute(
                    "INSERT INTO dailys_data (stat_name, stat_date, source, stat_data) VALUES (%s, %s, %s, %s) "
                    "ON CONFLICT (stat_name, stat_date) "
                    "DO UPDATE SET source=excluded.source, stat_data=excluded.stat_data",
                    (stat_name, update_date, source, json.dumps(new_data))
                )
                self.conn.commit()

    def get_latest_n_entries_for_stat(self, stat_name: str, n: int) -> List[DailysData]:
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT stat_data FROM dailys_data WHERE stat_name = %s ORDER BY stat_date DESC LIMIT %s",
                    (stat_name, n)
                )
                return [row["stat_data"] for row in cur.fetchall()]
