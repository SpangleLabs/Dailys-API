from collections import defaultdict
from typing import Dict, List, Optional

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
        self.raw_data = json_data["data"]

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