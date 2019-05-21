from datetime import time, datetime, timedelta

import flask
import firebase_admin
import numpy
from firebase_admin import firestore

from flask import request, abort

from models import SleepData, FuraffinityData, MoodMeasurement
from path_converters import DateConverter, EndDateConverter, SpecifiedDayConverter, StartDateConverter

app = flask.Flask(__name__)
app.url_map.converters['date'] = DateConverter
app.url_map.converters['start_date'] = StartDateConverter
app.url_map.converters['end_date'] = EndDateConverter
app.url_map.converters['view_date'] = SpecifiedDayConverter

firebase_admin.initialize_app()
DATA_SOURCE = firestore.client().collection('Dailys stats')


@app.route("/")
def hello_world():
    return "Hello, World! This is Spangle's dailys recording system."


def get_unique_stat_names():
    unique_names = set()
    for stat in DATA_SOURCE.get():
        if stat.get("stat_name"):
            unique_names.add(stat.get("stat_name"))
    return unique_names


@app.route("/stats/")
def list_stats():
    return flask.jsonify(list(get_unique_stat_names()))


@app.route("/stats/<stat_name>/")
def stat_data(stat_name):
    return flask.jsonify([x.to_dict() for x in DATA_SOURCE.where("stat_name", "==", stat_name).order_by("date").get()])


def get_stat_for_date(stat_name, view_date):
    data_partial = DATA_SOURCE.where("stat_name", "==", stat_name)
    if view_date == "latest":
        data_partial = data_partial.order_by("date").limit(1)
    elif view_date == "static":
        data_partial = data_partial.where("date", "==", "static")
    else:
        start_datetime = datetime.combine(view_date, time(0, 0, 0))
        end_datetime = datetime.combine(view_date + timedelta(days=1), time(0, 0, 0))
        data_partial = data_partial.where("date", ">=", start_datetime).where("date", "<", end_datetime)
    return list(data_partial.get())


@app.route("/stats/<stat_name>/<view_date:view_date>/", methods=['GET'])
def stat_data_on_date(stat_name, view_date):
    data = get_stat_for_date(stat_name, view_date)
    return flask.jsonify([x.to_dict() for x in data])


@app.route("/stats/<stat_name>/<view_date:view_date>/", methods=['PUT'])
def update_stat_data_on_date(stat_name, view_date):
    # Construct new data object
    new_data = request.get_json()
    total_data = {'stat_name': stat_name}
    if view_date == "latest":
        abort(404)
    elif view_date == "static":
        total_data['date'] = "static"
    else:
        total_data['date'] = datetime.combine(view_date, time(0, 0, 0))
    total_data['source'] = request.args.get("source", "Unknown [via API]")
    total_data['data'] = new_data
    # See if data exists
    data = get_stat_for_date(stat_name, view_date)
    if len(data) == 1:
        DATA_SOURCE.document(data[0].id).set(total_data)
    else:
        DATA_SOURCE.add(total_data)
    return flask.jsonify(total_data)


# @app.route("/stats/<stat_name>/<view_date:view_date>/", methods=['DELETE'])
# def remove_stat_data_on_date(stat_name, view_date):
#     # See if data exists
#     data = get_stat_for_date(stat_name, view_date)
#     if len(data) == 0:
#         abort(404)
#     else:
#         for datum in data:
#             datum.reference.delete()
#         return "Deleted"


@app.route("/stats/<stat_name>/<start_date:start_date>/<end_date:end_date>")
def stat_data_with_date_range(stat_name, start_date, end_date):
    data_partial = DATA_SOURCE.where("stat_name", "==", stat_name)
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
    return flask.jsonify(data)


@app.route("/views/")
def list_views():
    views = ["sleep_time", "fa_notifications", "mood"]
    return flask.render_template("list_views.html", views=views)


class ColourScale:
    YELLOW = (255, 255, 0)
    GREEN = (87, 187, 138)
    RED = (230, 124, 115)
    WHITE = (255, 255, 255)
    DANDELION = (255, 214, 102)

    def __init__(self, start_val, end_val, start_colour, end_colour):
        self.start_value = start_val
        self.end_value = end_val
        self.start_colour = start_colour
        self.end_colour = end_colour

    def get_colour_for_value(self, value):
        if value is None or not isinstance(value, (int, float)):
            return "transparent"
        ratio = (value-self.start_value) / (self.end_value-self.start_value)
        colour = (
                self.start_colour[0] + ratio * (self.end_colour[0] - self.start_colour[0]),
                self.start_colour[1] + ratio * (self.end_colour[1] - self.start_colour[1]),
                self.start_colour[2] + ratio * (self.end_colour[2] - self.start_colour[2])
        )
        return "rgb({},{},{})".format(int(colour[0]), int(colour[1]), int(colour[2]))


class MidPointColourScale(ColourScale):
    def __init__(self, start_val, mid_val, end_val, start_colour, mid_colour, end_colour):
        super().__init__(start_val, end_val, start_colour, end_colour)
        self.mid_val = mid_val
        self.mid_colour = mid_colour
        self.low_scale = ColourScale(start_val, mid_val, start_colour, mid_colour)
        self.high_scale = ColourScale(mid_val, end_val, mid_colour, end_colour)

    def get_colour_for_value(self, value):
        if value is None:
            return "transparent"
        if value > self.mid_val:
            return self.high_scale.get_colour_for_value(value)
        else:
            return self.low_scale.get_colour_for_value(value)


@app.route("/views/sleep_time/<start_date:start_date>/<end_date:end_date>")
def view_sleep_stats_range(start_date, end_date):
    # Get data
    sleep_data_response = stat_data_with_date_range("sleep", start_date, end_date)
    sleep_data = [SleepData(x) for x in sleep_data_response.get_json()]
    # Generate total stats
    stats = {}
    time_sleeping_list = [x.time_sleeping for x in sleep_data]
    stats['max'] = max(time_sleeping_list)
    stats['min'] = min(time_sleeping_list)
    # noinspection PyUnresolvedReferences
    stats['avg'] = timedelta(seconds=round(numpy.mean(time_sleeping_list).total_seconds()))
    stats['stdev'] = numpy.std([x.total_seconds()/86400 for x in time_sleeping_list])
    stats['total'] = sum([x.total_seconds()/86400 for x in time_sleeping_list])
    # Generate weekly stats
    weekly_stats = {}
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for day in [0, 1, 2, 3, 4, 5, 6, "weekday", "weekend"]:
        weekly_stats[day] = {}
        weekly_stats[day]['sleeps'] = []
        if isinstance(day, int):
            weekly_stats[day]['name'] = weekdays[day]
        else:
            weekly_stats[day]['name'] = day.title()
    for sleep_datum in sleep_data:
        weekday = (sleep_datum.date.weekday()+1) % 7
        weekly_stats[weekday]['sleeps'].append(sleep_datum.time_sleeping.total_seconds())
        if weekday in [5, 6]:
            weekly_stats["weekend"]['sleeps'].append(sleep_datum.time_sleeping.total_seconds())
        else:
            weekly_stats['weekday']['sleeps'].append(sleep_datum.time_sleeping.total_seconds())
    for day in weekly_stats.keys():
        weekly_stats[day]['avg'] = timedelta(seconds=round(numpy.mean(weekly_stats[day]['sleeps'])))
    # Create scales
    stats_scale = MidPointColourScale(
        stats['min'], stats['avg'], stats['max'],
        ColourScale.YELLOW, ColourScale.WHITE, ColourScale.GREEN
    )
    weekly_scale = MidPointColourScale(
        min([x['avg'] for x in weekly_stats.values()]),
        stats['avg'],
        max([x['avg'] for x in weekly_stats.values()]),
        ColourScale.YELLOW, ColourScale.WHITE, ColourScale.GREEN
    )
    # Return page
    return flask.render_template(
        "sleep_time.html",
        sleeps=sleep_data,
        stats=stats,
        weekly_stats=weekly_stats,
        stats_scale=stats_scale,
        weekly_scale=weekly_scale
    )


@app.route("/views/sleep_time/")
def view_sleep_stats():
    return view_sleep_stats_range("earliest", "latest")


@app.route("/views/fa_notifications/<start_date:start_date>/<end_date:end_date>")
def view_fa_notifications_range(start_date, end_date):
    # Get data
    fa_data_response = stat_data_with_date_range("furaffinity", start_date, end_date)
    fa_data = {
        FuraffinityData(x).date: {"data": FuraffinityData(x)}
        for x in fa_data_response.get_json()
    }
    # Add in diff data
    for today in fa_data.keys():
        yesterday = today - timedelta(days=1)
        fa_data[today]['diff'] = None
        if yesterday in fa_data:
            diff = fa_data[today]['data'].total - fa_data[yesterday]['data'].total
            if diff >= 0:
                fa_data[today]['diff'] = diff
    # Create colour scale
    max_notif = max([x['data'].total for x in fa_data.values()])
    scale = ColourScale(0, max_notif, ColourScale.WHITE, ColourScale.RED)
    # Render template
    return flask.render_template("fa_notifications.html", fa_notifications=fa_data, scale=scale)


@app.route("/views/fa_notifications/")
def view_fa_notification_stats():
    return view_fa_notifications_range("earliest", "latest")


@app.route("/views/mood/<start_date:start_date>/<end_date:end_date>")
def view_mood_stats_range(start_date, end_date):
    # Get static mood data
    mood_static = stat_data_on_date("mood", "static").get_json()[0]['data']
    # Get mood data
    mood_data_response = stat_data_with_date_range("mood", start_date, end_date)
    mood_data = mood_data_response.get_json()
    # Get sleep data, if necessary
    sleep_data = {}
    if "WakeUpTime" in mood_static['times'] or "SleepTime" in mood_static['times']:
        sleep_data_response = stat_data_with_date_range("sleep", start_date, end_date)
        sleep_data = {SleepData(x).date: SleepData(x) for x in sleep_data_response.get_json()}
    # Create list of mood measurements
    mood_measurements = [
        MoodMeasurement(x, mood_time, sleep_data)
        for x in mood_data
        for mood_time in mood_static['times']
        if mood_time in x['data']
    ]
    # Create scales
    scale = ColourScale(1, 5, ColourScale.WHITE, ColourScale.DANDELION)
    # TODO: define what mood measurements are good vs bad
    scale_good = ColourScale(1, 5, ColourScale.WHITE, ColourScale.GREEN)
    scale_bad = ColourScale(1, 5, ColourScale.WHITE, ColourScale.RED)
    # Render template
    return flask.render_template(
        "mood.html",
        mood_static=mood_static,
        mood_measurements=mood_measurements,
        scale=scale,
        scale_good=scale_good,
        scale_bad=scale_bad
    )


@app.route("/views/mood/")
def view_mood_stats():
    return view_mood_stats_range("earliest", "latest")
