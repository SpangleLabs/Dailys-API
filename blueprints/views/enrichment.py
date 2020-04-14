from collections import namedtuple

import flask

from blueprints.views.base_view import View

EnrichmentSuggestion = namedtuple(
    "EnrichmentSuggestion",
    ["datum", "enrichment"]
)


class EnrichmentView(View):
    def get_path(self):
        return "/enrichment/"

    def call(self, **kwargs):
        all_data = self.data_source.get_entries_over_range("earliest", "latest")
        suggestions = []
        for entry in all_data:
            suggestion = self.suggest_enrichment(entry)
            if suggestion is not None:
                suggestions.append(suggestion)
        return flask.render_template(
            "enrichment.html",
            suggestions=suggestions
        )

    def suggest_enrichment(self, datum):
        enrichment_checkers = {
            "sleep": None,
            "duolingo": None,
            "chores": None,
            "furaffinity": None,
            "dreams": self.suggest_enrichment_dream,
            "mood": None
        }
        stat_name = datum["stat_name"]
        suggestion_unknown = EnrichmentSuggestion(
            datum,
            f"Unknown stat type {stat_name}. Could be added to enrichment checker."
        )
        checker = enrichment_checkers.get(stat_name, lambda x: suggestion_unknown)
        if checker is None:
            return None
        return checker(datum)

    def suggest_enrichment_dream(self, datum):
        suggestions = []
        for dream_idx in range(len(datum["data"]["dreams"])):
            dream = datum["data"]["dreams"][dream_idx]
            if "disorientation" not in dream:
                suggestions.append(f"Dream {dream_idx} could add disorientation rating.")
            if "lewdness" not in dream:
                suggestions.append(f"Dream {dream_idx} could add lewdness rating.")
            if "false_facts" not in dream:
                suggestions.append(f"Dream {dream_idx} could list false facts.")
            if "famous_people" not in dream:
                suggestions.append(f"Dream {dream_idx} could tag famous people.")
            if "known_people" not in dream:
                suggestions.append(f"Dream {dream_idx} could tag known people.")
            if "tags" not in dream:
                suggestions.append(f"Dream {dream_idx} could add tags.")
        if not suggestions:
            return None
        return EnrichmentSuggestion(
            datum,
            "\n".join(suggestions)
        )


class EnrichmentFormView(View):

    def get_path(self):
        return "/enrichment/<stat_name>/<view_date:view_date>/"

    def call(self, **kwargs):
        stat_name = kwargs["stat_name"]
        enrichment_page = {
            "sleep": None,
            "duolingo": None,
            "chores": None,
            "furaffinity": None,
            "dreams": self.call_dream,
            "mood": None
        }
        view_date = kwargs["view_date"]
        page_func = enrichment_page.get(stat_name)
        if page_func is None:
            return f"I've got no enrichment form set up for {stat_name}."
        page = page_func(view_date)
        if page is None:
            return "This data does not need enrichment"
        return page

    def call_dream(self, view_date):
        entries = self.data_source.get_entries_for_stat_on_date("dreams", view_date)
        if not entries:
            return None
        return flask.render_template(
            "enrichment_forms/dreams.html",
            entry=entries[0]
        )
