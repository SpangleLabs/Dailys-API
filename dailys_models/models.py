from typing import Dict, List

from dailys_web.data_source.data_source import DailysEntry, DailysData


class Data:

    def __init__(self, json_data: DailysEntry):
        self.raw_data = json_data
        self.date = json_data['date']
        self.source = json_data['source']
        self.stat_name = json_data['stat_name']

    def suggest_enrichments(self) -> Dict[str, List[str]]:
        return {}

    @property
    def date_str(self) -> str:
        return self.date.date().isoformat()

    @property
    def url_path(self) -> str:
        return f"/{self.stat_name}/{self.date_str}/"

    def enriched_data(self, form_data) -> DailysData:
        return self.raw_data

    def enrichment_form(self, data_source):
        return "There is no enrichment form set up for this stat type"
