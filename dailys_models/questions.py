import dateutil.parser
from datetime import datetime, date
from typing import Dict

from dailys_models.models import Data
from dailys_web.data_source.data_source import DailysEntry


class Response:
    def __init__(self, answer: str, answer_time: datetime) -> None:
        self.answer = answer
        self.answer_time = answer_time


class Answer:
    def __init__(self, answer_data: Dict) -> None:
        self.question_id = answer_data["question_id"]
        self.asked_time = dateutil.parser.parse(answer_data["asked_time"])
        self.responses = []
        if "edit_history" in answer_data:
            for resp_data in answer_data["edit_history"]:
                self.responses.append(Response(
                    resp_data["answer"],
                    dateutil.parser.parse(resp_data["answer_time"])
                ))
        if "answer" in answer_data:
            self.responses.append(Response(
                answer_data["answer"],
                dateutil.parser.parse(answer_data["answer_time"])
            ))

    @property
    def is_answered(self) -> bool:
        return bool(self.responses)


class QuestionsDay(Data):
    def __init__(self, json_data: DailysEntry):
        super().__init__(json_data)
        self.answers = {}
        for answer_data in self.raw_data["data"]["answers"]:
            answer = Answer(answer_data)
            self.answers[answer.question_id] = answer
    
    def count_answers(self) -> int:
        return len([answer for answer in self.answers.values() if answer.is_answered])
    
    def value_count(self) -> int:
        return self.count_answers()


class StaticQuestion:

    def __init__(self, static_data: Dict) -> None:
        self.static_data = static_data
        self.id = static_data["id"]
        self.creation_date = dateutil.parser.parse(static_data["creation"])
        self.question_text = static_data["question"]
        self.time_pattern_str = static_data["time_pattern"]
        self.deprecation_date = None
        if "deprecation" in static_data:
            self.deprecation_date = dateutil.parser.parse(static_data["deprecation"])

    @property
    def is_active(self) -> bool:
        return self.deprecation_date is None

    def count_prompts(self, answer_date_dict: Dict[date, QuestionsDay]) -> int:
        return sum(
            1
            for answer_day in answer_date_dict.values()
            if self.id in answer_day.answers
        )

    def count_answers(self, answer_date_dict: Dict[date, QuestionsDay]) -> int:
        return sum(
            1
            for answer_day in answer_date_dict.values()
            if self.id in answer_day.answers
            and answer_day.answers[self.id].is_answered
        )