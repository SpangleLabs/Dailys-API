import flask

from dailys_models.model_dict import MODEL_DICT
from dailys_web.blueprints.views.base_view import View
from dailys_web.nav_data import NavData


class StatsRangeView(View):
    def get_path(self):
        return "/stats/<start_date:start_date>/<end_date:end_date>/"

    def call(self, **kwargs):
        start_date = kwargs["start_date"]
        end_date = kwargs["end_date"]
        stat_list = self.data_source.get_entries_over_range(start_date, end_date)
        # Calculations for stats -> values
        value_calc = {
            "mood": lambda x: len(x.keys()) * len([y for y in x[list(x)[0]].keys() if y != "message_id"]),
            "duolingo": lambda x: len(x.keys()),
            "chores": lambda x: len(x['chores_done'])
        }
        # Calculate date and source totals
        date_totals = {}
        source_totals = {}
        stat_totals = {}
        for stat in stat_list:
            stat_name = stat["stat_name"]
            stat_date = stat["date"].date()
            source = stat["source"]
            # Create data object, if applicable
            if MODEL_DICT.get(stat_name) is not None:
                stat_data = MODEL_DICT[stat_name](stat)
                values_count = stat_data.value_count()
            else:
                values_count = value_calc.get(stat_name, lambda x: 0)(stat["data"])
            # Update date totals
            if stat_date not in date_totals:
                date_totals[stat_date] = {"stats": 0, "values": 0, "values_by_stat": {}}
            date_totals[stat_date]['stats'] += 1
            date_totals[stat_date]['values'] += values_count
            date_totals[stat_date]['values_by_stat'][stat_name] = values_count
            # Update source totals
            if source not in source_totals:
                source_totals[source] = {"stats": 0, "values": 0}
            source_totals[source]["stats"] += 1
            source_totals[source]["values"] += values_count
            # Update stat totals
            if stat_name not in stat_totals:
                stat_totals[stat_name] = {"stats": 0, "values": 0}
            stat_totals[stat_name]["stats"] += 1
            stat_totals[stat_name]["values"] += values_count
        # Sum up totals
        total_stats = sum([source_totals[x]['stats'] for x in source_totals.keys()])
        total_values = sum([source_totals[x]['values'] for x in source_totals.keys()])

        return flask.render_template(
            "total_stats.html",
            nav_data=NavData(),
            total_stats=total_stats,
            total_values=total_values,
            date_totals=date_totals,
            source_totals=source_totals,
            stat_totals=stat_totals
        )


class StatsView(StatsRangeView):

    def get_path(self):
        return "/stats/"

    def call(self, **kwargs):
        return super().call(start_date="earliest", end_date="latest")
