from collections import defaultdict
from typing import NamedTuple, List, Dict

import flask

from blueprints.views.base_view import View
from data_source import DailysEntry
from models.dream_night import DreamNight
from models.fa_data import FuraffinityData
from models.model_dict import MODEL_DICT
from models.sleep_data import SleepData


class EnrichmentSuggestion(NamedTuple):
    datum: DailysEntry
    # The data entry the suggestions are for

    suggestions: Dict[str, List[str]]
    # A dict of suggestion to a list of json paths


class EnrichmentView(View):
    def get_path(self):
        return "/enrichment/"

    def call(self, **kwargs):
        all_data = self.data_source.get_entries_over_range("earliest", "latest")
        # Get list of all suggestions
        suggestions = []
        for entry in all_data:
            suggestion = self.suggest_enrichment(entry)
            if suggestion is not None:
                suggestions.append(suggestion)
        # Collate totals.
        totals = self.total_suggestions(suggestions)
        # Render
        return flask.render_template(
            "enrichment.html",
            suggestions=suggestions,
            totals=totals
        )

    def total_suggestions(self, suggestions):
        totals = defaultdict(
            lambda: {"total": 0, "suggestion_totals": defaultdict(lambda: {"total_entries": 0, "total_paths": 0})})
        for suggestion in suggestions:
            stat_name = suggestion.datum["stat_name"]
            totals[stat_name]["total"] += 1
            for sub_sug, paths in suggestion.suggestions.items():
                totals[stat_name]["suggestion_totals"][sub_sug]["total_entries"] += 1
                totals[stat_name]["suggestion_totals"][sub_sug]["total_paths"] += len(paths)
        return totals

    def suggest_enrichment(self, datum):
        stat_name = datum["stat_name"]
        suggestion_unknown = EnrichmentSuggestion(
            datum,
            {
                f"stat type {stat_name}, could be added to enrichment.py.": ["."]
            }
        )
        if stat_name not in MODEL_DICT:
            return suggestion_unknown
        model_class = MODEL_DICT[stat_name]
        if model_class is None:
            return None
        entry_object = model_class(datum)
        suggestions = entry_object.suggest_enrichments()
        if not suggestions:
            return None
        return EnrichmentSuggestion(datum, suggestions)


class EnrichmentFormView(View):

    def get_path(self):
        return "/enrichment/<stat_name>/<view_date:view_date>/"

    def call(self, **kwargs):
        stat_name = kwargs["stat_name"]
        view_date = kwargs["view_date"]
        # Get model
        model_class = MODEL_DICT.get(stat_name)
        if model_class is None:
            return f"There is no model for {stat_name}."
        # Get data
        entries = self.data_source.get_entries_for_stat_on_date("dreams", view_date)
        if len(entries) != 1:
            return f"There is no entry for stat type {stat_name} on date {view_date}"
        model = model_class(entries[0])
        return model.enrichment_form(self.data_source)
