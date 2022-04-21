import dateutil.parser
from datetime import datetime

from dailys_models.models import Data


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
        for answer_data in self.raw_data["answers"]:
            answer = Answer(answer_data)
            self.answers[answer.question_id] = answer
    
    def value_count(self) -> int:
        return len(answer for answer in self.answers.values() if answer.is_answered)
