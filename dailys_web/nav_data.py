import flask

from dailys_web.path_converters import NAMED_DATES


class NavData:
    def __init__(self):
        self.list_views = ["sleep_time", "fa_notifications", "stats", "mood", "mood_weekly", "dreams"]
        current_path = flask.request.path.strip("/").split("/")
        self.current_view = current_path[1]
        self.start_date = "earliest"
        self.end_date = "latest"
        if len(current_path) > 2:
            self.start_date = current_path[2]
            self.end_date = current_path[3]
        self.named_dates = NAMED_DATES
