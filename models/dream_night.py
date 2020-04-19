from collections import defaultdict
from typing import Dict, List

import flask

from data_source import DailysData
from models.models import Data


class Dream:

    def __init__(self, data):
        self.data = data
        self.text = data["text"]
        self.disorientation = data.get("disorientation")
        self.lewdness = data.get("lewdness")


class DreamNight(Data):

    def __init__(self, json_data):
        super().__init__(json_data)
        self.dreams = [Dream(x) for x in json_data["data"]["dreams"]]

    def dream_preview(self, length=50):
        if len(self.dreams) == 0:
            return ""
        first_dream = self.dreams[0]
        if len(first_dream.text) < 50:
            return first_dream.text
        return first_dream.text[:length] + "..."

    @property
    def dream_count(self):
        return len(self.dreams)

    @property
    def total_dreams_length(self):
        return sum(len(dream.text) for dream in self.dreams)

    @property
    def max_disorientation(self):
        dream_values = [dream.disorientation for dream in self.dreams]
        if list(filter(None, dream_values)):
            return max(filter(None, dream_values))
        return "-"

    @property
    def max_lewdness(self):
        dream_values = [dream.lewdness for dream in self.dreams]
        if list(filter(None, dream_values)):
            return max(filter(None, dream_values))
        return "-"

    def suggest_enrichments(self) -> Dict[str, List[str]]:
        suggestions = defaultdict(lambda: [])
        for dream_idx in range(len(self.dreams)):
            dream_data = self.dreams[dream_idx].data
            sub_target = f"$.data.dreams[{dream_idx}]"
            if "disorientation" not in dream_data:
                suggestions["could add disorientation rating"].append(sub_target)
            if "lewdness" not in dream_data:
                suggestions["could add lewdness rating"].append(sub_target)
            if "false_facts" not in dream_data:
                suggestions["could list false facts"].append(sub_target)
            if "famous_people" not in dream_data:
                suggestions["could tag famous people."].append(sub_target)
            if "known_people" not in dream_data:
                suggestions["could tag known people."].append(sub_target)
            if "tags" not in dream_data:
                suggestions["could add tags."].append(sub_target)
        if not suggestions:
            return {}
        return suggestions

    def enriched_data(self, form_data) -> DailysData:
        raw_data = self.raw_data["data"]
        for dream_idx in range(len(self.dreams)):
            if f"disorientation-{dream_idx}" in form_data:
                disorientation = int(form_data[f"disorientation-{dream_idx}"])
                raw_data["dreams"][dream_idx]["disorientation"] = disorientation
            if f"lewdness-{dream_idx}" in form_data:
                lewdness = int(form_data[f"lewdness-{dream_idx}"])
                raw_data["dreams"][dream_idx]["lewdness"] = lewdness
            if f"false_facts-{dream_idx}" in form_data:
                false_facts = [fact.strip() for fact in form_data[f"false_facts-{dream_idx}"].split("|") if fact != ""]
                raw_data["dreams"][dream_idx]["false_facts"] = false_facts
            if f"famous_people-{dream_idx}" in form_data:
                famous_people = [person.strip() for person in form_data[f"famous_people-{dream_idx}"].split("|") if person != ""]
                raw_data["dreams"][dream_idx]["famous_people"] = famous_people
            if f"known_people-{dream_idx}" in form_data:
                known_people = [person.strip() for person in form_data[f"known_people-{dream_idx}"].split("|") if person != ""]
                raw_data["dreams"][dream_idx]["known_people"] = known_people
            if f"tags-{dream_idx}" in form_data:
                tags = [tag.strip() for tag in form_data[f"tags-{dream_idx}"].split("|") if tag != ""]
                raw_data["dreams"][dream_idx]["tags"] = tags
        return raw_data

    def enrichment_form(self, data_source):
        # Get lists of tags and stuff
        all_entries = data_source.get_entries_for_stat_over_range("dreams", "earliest", "latest")
        tags = set()
        known_people = set()
        famous_people = set()
        for entry in all_entries:
            for dream in entry["data"]["dreams"]:
                tags.update(dream.get("tags", []))
                known_people.update(dream.get("known_people", []))
                famous_people.update(dream.get("famous_people", []))
        return flask.render_template(
            "enrichment_forms/dreams.html",
            dream_night=self,
            entry=self.raw_data,
            tags=tags,
            known_people=known_people,
            famous_people=famous_people
        )
