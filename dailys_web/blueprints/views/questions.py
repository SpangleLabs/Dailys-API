from typing import Dict, List
from datetime import date

import dateutil.parser
import flask

from dailys_models.questions import QuestionsDay
from dailys_web.blueprints.views.base_view import View
from dailys_web.nav_data import NavData


class Question:
  
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


class QuestionStats:
    def __init__(self, questions: List[Question], answers: List[QuestionsDay]):
        self.questions = questions
        self.answers = answers
    
    @property
    def total_questions(self) -> int:
        return len(self.questions)
      
    @property
    def active_questions(self) -> int:
        return sum(1 for question in self.questions if question.is_active)
    
    @property
    def days_with_prompts(self) -> int:
        return len(self.answers)
    
    @property
    def total_prompts(self) -> int:
        return sum((len(answer_day.answers) for answer_day in self.answers))

    @property
    def total_answers(self) -> int:
        return sum(answer_day.count_answers() for answer_day in self.answers)
      

class QuestionsRangeView(View):
    def get_path(self) -> str:
        return "/questions/<start_date:start_date>/<end_date:end_date>/"
  
    def call(self, **kwargs):
        start_date = kwargs["start_date"]
        end_date = kwargs["end_date"]
        # Get question data
        q_static = self.data_source.get_entries_for_stat_on_date("questions", "static")[0]['data']
        questions = [Question(data) for data in q_static["questions"]]
        # Get answers data
        answers_data = self.data_source.get_entries_for_stat_over_range("questions", start_date, end_date)
        answers_days = [QuestionsDay(data) for data in answers_data]
        answers_date_dict = {day.date: day for day in answers_days}
        # Get stats object
        stats = QuestionStats(questions, answers_days)
        return flask.render_template(
            "questions.html",
            nav_data=NavData(),
            stats=stats,
            questions=questions,
            answers_dict=answers_date_dict
        )


class QuestionsView(QuestionsRangeView):
    def get_path(self) -> str:
        return "/questions/"
    
    def call(self, **kwargs):
        return super().call(start_date="earliest", end_date="latest")
