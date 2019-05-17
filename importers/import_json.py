import json
# noinspection PyPackageRequirements
from json import JSONDecodeError

import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:5000"
STAT_NAME = None  # TODO: set
START_DATE = date(2016, 6, 6)  # TODO: set
SOURCE = None  # TODO: set


def read_json_list(file_name):
    data_list = []
    with open(file_name, "r") as f:
        for line in f.readlines():
            try:
                data_list.append(json.loads(line))
            except JSONDecodeError:
                data_list.append(None)
    return data_list


def upload_data(post_url, post_data):
    response = requests.put(url=post_url, json=post_data)
    return response


if __name__ == "__main__":
    data = read_json_list("raw_data.txt")
    date = START_DATE
    for datum in data:
        if datum is not None:
            url = "{}/stats/{}/{}?source={}".format(BASE_URL, STAT_NAME, date, SOURCE)
            resp = upload_data(url, datum)
            print(resp)
        date += timedelta(days=1)
