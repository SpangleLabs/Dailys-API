import json
from datetime import datetime, time
from typing import Dict, Set, List

import psycopg2
from psycopg2.extras import RealDictCursor

from dailys_web.data_source.data_source import DailysEntry, DataSource, DailysEntries, DailysDate, DailysData


def entry_from_row(row: Dict) -> DailysEntry:
    return {
        "stat_name": row["stat_name"],
        "source": row["source"],
        "date": datetime.combine(row["stat_date"], time(0, 0, 0)),
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
                if view_date in ["earliest", "latest"]:
                    raise ValueError("Cannot delete earliest/latest stat entry")
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
                if view_date == "earliest":
                    cur.execute(
                        "SELECT stat_name, stat_date, source, stat_data FROM dailys_data "
                        "WHERE stat_name = %s ORDER BY stat_date ASC LIMIT 1",
                        (stat_name,)
                    )
                elif view_date == "latest":
                    cur.execute(
                        "SELECT stat_name, stat_date, source, stat_data FROM dailys_data "
                        "WHERE stat_name = %s ORDER BY stat_date DESC LIMIT 1",
                        (stat_name,)
                    )
                else:
                    cur.execute(
                        "SELECT stat_name, stat_date, source, stat_data FROM dailys_data "
                        "WHERE stat_name = %s AND stat_date = %s",
                        (stat_name, view_date)
                    )
                return [entry_from_row(row) for row in cur.fetchall()]

    def get_entries_over_range(self, start_date: DailysDate, end_date: DailysDate) -> DailysEntries:
        with self.conn:
            with self.conn.cursor() as cur:
                if start_date == "earliest":
                    if end_date == "latest":
                        cur.execute(
                            "SELECT stat_name, stat_date, source, stat_data FROM dailys_data "
                            "ORDER BY stat_date"
                        )
                    else:
                        cur.execute(
                            "SELECT stat_name, stat_date, source, stat_data FROM dailys_data "
                            "WHERE stat_date <= %s "
                            "ORDER BY stat_date",
                            (end_date,)
                        )
                else:
                    if end_date == "latest":
                        cur.execute(
                            "SELECT stat_name, stat_date, source, stat_data FROM dailys_data "
                            "WHERE stat_date >= %s "
                            "ORDER BY stat_date",
                            (start_date,)
                        )
                    else:
                        cur.execute(
                            "SELECT stat_name, stat_date, source, stat_data FROM dailys_data "
                            "WHERE stat_date >= %s AND stat_date <= %s "
                            "ORDER BY stat_date",
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
                if start_date == "earliest":
                    if end_date == "latest":
                        cur.execute(
                            "SELECT stat_name, stat_date, source, stat_data FROM dailys_data "
                            "WHERE stat_name = %s "
                            "ORDER BY stat_date",
                            (stat_name,)
                        )
                    else:
                        cur.execute(
                            "SELECT stat_name, stat_date, source, stat_data FROM dailys_data "
                            "WHERE stat_name = %s AND stat_date <= %s "
                            "ORDER BY stat_date",
                            (stat_name, end_date)
                        )
                else:
                    if end_date == "latest":
                        cur.execute(
                            "SELECT stat_name, stat_date, source, stat_data FROM dailys_data "
                            "WHERE stat_name = %s AND stat_date >= %s "
                            "ORDER BY stat_date",
                            (stat_name, start_date)
                        )
                    else:
                        cur.execute(
                            "SELECT stat_name, stat_date, source, stat_data FROM dailys_data "
                            "WHERE stat_name = %s AND stat_date >= %s AND stat_date <= %s "
                            "ORDER BY stat_date",
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
                if update_date in ["earliest", "latest"]:
                    raise ValueError("Can't update data on earliest/latest")
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