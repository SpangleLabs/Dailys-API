from typing import Dict, List

from data_source import DailysEntry


class Data:

    def __init__(self, json_data: DailysEntry):
        self.date = json_data['date']
        self.source = json_data['source']
        self.stat_name = json_data['stat_name']

    def suggest_enrichments(self) -> Dict[str, List[str]]:
        return {}

    @property
    def url_path(self) -> str:
        return f"/{self.stat_name}/{self.date.date().isoformat()}/"
