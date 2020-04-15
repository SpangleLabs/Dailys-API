from collections import namedtuple, defaultdict
from datetime import datetime, time

import dateutil
import flask
from dateutil.relativedelta import relativedelta

from blueprints.views.base_view import View
from colour_scale import ColourScale
from models.dream_night import DreamNight

DreamStats = namedtuple("DreamStats", [
    "count_with_dreams",
    "count_without_dreams",
    "percentage_with_dreams",
    "max_dreams",
    "max_length"
])


# noinspection PyMethodMayBeStatic
class DreamsRangeView(View):
    def get_path(self):
        return "/dreams/<start_date:start_date>/<end_date:end_date>"

    def call(self, **kwargs):
        start_date = kwargs["start_date"]
        end_date = kwargs["end_date"]
        dream_nights = self.get_dream_nights(start_date, end_date)
        # Get nights by week
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dream_nights_weekly = self.dream_nights_by_week(dream_nights, weekdays)
        # Stats
        stats = self.get_dream_stats(dream_nights)
        # Scales
        dream_count_scale = ColourScale(
            0, max(len(night.dreams) for night in dream_nights),
            ColourScale.WHITE, ColourScale.RED
        )
        dream_length_scale = ColourScale(
            0, max(night.total_dreams_length for night in dream_nights),
            ColourScale.WHITE, ColourScale.RED
        )
        rating_scale = ColourScale(
            1, 5, ColourScale.WHITE, ColourScale.RED
        )
        return flask.render_template(
            "dreams.html",
            dream_nights=dream_nights,
            stats=stats,
            weekdays=weekdays,
            dream_nights_weekly=dream_nights_weekly,
            dream_count_scale=dream_count_scale,
            dream_length_scale=dream_length_scale,
            rating_scale=rating_scale
        )

    def get_dream_nights(self, start_date, end_date):
        dreams_data = self.data_source.get_entries_for_stat_over_range("dreams", start_date, end_date)
        dream_nights = [DreamNight(x) for x in dreams_data]
        static_data = self.data_source.get_entries_for_stat_on_date("dreams", "static")
        # Fill in missing dates
        if static_data and "all_nights_start" in static_data[0]["data"]:
            dream_dates = [night.date.date() for night in dream_nights]
            start_date = dateutil.parser.parse(static_data[0]["data"]["all_nights_start"]).date()
            end_date = max(dream_dates)
            current_date = max(start_date, min(dream_dates))
            while current_date <= end_date:
                if current_date not in dream_dates:
                    dream_nights.append(DreamNight(
                        {"date": datetime.combine(current_date, time(0, 0, 0)), "source": "Auto-generated",
                         "stat_name": "dreams", "data": {"dreams": []}}))
                current_date += relativedelta(days=1)
            dream_nights.sort(key=lambda x: x.date.date())
        return dream_nights

    def dream_nights_by_week(self, dream_nights, weekdays):
        weekly = defaultdict(lambda: {key: None for key in weekdays})
        for night in dream_nights:
            weekly[night.date.strftime("%G-%V")][night.date.strftime("%A")] = night
        return weekly

    def get_dream_stats(self, dream_nights):
        count_with_dreams = len([night for night in dream_nights if night.dream_count > 0])
        count_without_dreams = len(dream_nights) - count_with_dreams
        percentage_with_dreams = f"{100 * (count_with_dreams / len(dream_nights)):.2f}%"
        max_dreams = max([night.dream_count for night in dream_nights])
        max_length = max([night.total_dreams_length for night in dream_nights])
        return DreamStats(
            count_with_dreams,
            count_without_dreams,
            percentage_with_dreams,
            max_dreams,
            max_length
        )


class DreamsView(DreamsRangeView):
    def get_path(self):
        return "/dreams/"

    def call(self, **kwargs):
        return super().call(start_date="earliest", end_date="latest")
