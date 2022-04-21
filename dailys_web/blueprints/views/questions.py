from typing import List

import flask

from dailys_models.questions import QuestionsDay, StaticQuestion
from dailys_web.blueprints.views.base_view import View
from dailys_web.nav_data import NavData


class QuestionStats:
    def __init__(self, questions: List[StaticQuestion], answers: List[QuestionsDay]):
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
        questions = [StaticQuestion(data) for data in q_static["questions"]]
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
