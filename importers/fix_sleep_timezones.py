import datetime

import dateutil.parser
from dateutil.tz import tzutc

from data_source import DataSource


def add_tz_if_missing(dt_str: str) -> str:
    dt = dateutil.parser.parse(dt_str)
    if dt.tzinfo:
        return dt_str
    return dt.replace(tzinfo=tzutc()).isoformat()


if __name__ == "__main__":
    data_source = DataSource()
    start_date = datetime.datetime(2016, 4, 11)
    end_date = datetime.datetime(2020, 10, 25)
    sleep_data_resp = data_source.get_entries_for_stat_over_range("sleep", start_date, end_date)
    for sleep_stat in sleep_data_resp:
        sleep_datum = sleep_stat["data"]
        print(sleep_stat)
        sleep_datum['sleep_time'] = add_tz_if_missing(sleep_datum['sleep_time'])
        sleep_datum['wake_time'] = add_tz_if_missing(sleep_datum['wake_time'])
        for i in sleep_datum.get('interruptions', []):
            if "sleep_time" in i:
                i['sleep_time'] = add_tz_if_missing(i["sleep_time"])
            if "wake_time" in i:
                i['wake_time'] = add_tz_if_missing(i['wake_time'])
        print(sleep_stat)
        data_source.update_entry_for_stat_on_date("sleep", sleep_stat["date"], sleep_datum, sleep_stat["source"])
