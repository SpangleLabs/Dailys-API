import math
from datetime import date

import flask
import isodate

from blueprints.views.base_view import View
from colour_scale import ColourScale
from models.chores import Chore


class ChoresBoardJsonView(View):
    def get_path(self):
        return "/chores_board.json"

    def call(self, **kwargs):
        today = date.today()
        chores_static = self.data_source.get_entries_for_stat_on_date("chores", "static")[0]
        chores_data = self.data_source.get_entries_for_stat_over_range("chores", "earliest", "latest")
        chores = [Chore(x) for x in chores_static['data']['chores']]
        for chore_date in chores_data:
            for chore in chores:
                chore.parse_date_entry(chore_date)
        # Sort chores into categories
        categorised_chores = dict()
        for chore in chores:
            if chore.category not in categorised_chores:
                categorised_chores[chore.category] = []
            categorised_chores[chore.category].append(chore)
        # Get layout info
        layout = chores_static['data']['layout']
        # Return json
        return flask.jsonify({
            "today": isodate.date_isoformat(today),
            "chores": {k: [x.to_json() for x in v] for k, v in categorised_chores.items()},
            "layout": layout
        })


class ChoresBoardView(ChoresBoardJsonView):
    def get_path(self):
        return "/chores_board/"

    def call(self, **kwargs):
        chores_board = super().call().get_json()
        today = isodate.parse_date(chores_board['today'])
        categorised_chores = {k: [Chore.from_complete_json(x) for x in v] for k, v in chores_board['chores'].items()}
        layout = chores_board['layout']
        # Calculate overdue and neglected chores
        overdue_chores = []
        neglected_chores = []
        for chore_list in categorised_chores.values():
            for chore in chore_list:
                if chore.recommended_period is not None:
                    if chore.is_overdue():
                        overdue_chores.append(chore)
                else:
                    neglected_chores.append(chore)
        # Sort overdue and neglected chores lists
        overdue_chores.sort(key=lambda x: x.days_overdue(), reverse=True)
        neglected_chores.sort(key=lambda x: x.days_since_done() or math.inf, reverse=True)
        # Colour scales for non-recommended-period chores
        start_colouring = today - isodate.parse_duration("P2M")
        end_colouring = today - isodate.parse_duration("P1W")
        colour_scale = ColourScale(
            start_colouring, end_colouring,
            ColourScale.RED, ColourScale.WHITE
        )
        # Render
        return flask.render_template(
            "chores_board.html",
            today=today,
            categorised_chores=categorised_chores,
            layout=layout,
            overdue_chores=overdue_chores,
            neglected_chores=neglected_chores,
            colour_scale=colour_scale,
        )
