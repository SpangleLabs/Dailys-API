import json
# noinspection PyPackageRequirements
from json import JSONDecodeError

import requests
from datetime import date, timedelta

BASE_URL = "http://dailys-240210.appspot.com"
STAT_NAME = "sleep"  # TODO: set
DATE = date(2019, 8, 3)  # TODO: set
SOURCE = "Manual"  # TODO: set


def upload_data(post_url, post_data):
    response = requests.put\
        (
            url=post_url,
            json=post_data,
            headers={"Authorization": "3698a18e-3c20-41f8-bc60-265cc7deaac7"}
        )
    return response


if __name__ == "__main__":
    url = "{}/stats/{}/{}?source={}".format(BASE_URL, STAT_NAME, DATE, SOURCE)
    print(url)
    resp = upload_data(url, {})
    print(resp)
