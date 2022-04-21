from typing import Dict

from dailys_models.questions import QuestionsDay
from dailys_web.blueprints.views.base_view import View


class Question:
  
    def __init__(self, static_data: Dict) -> None:
        self.static_data = static_data
        self.id = static_data["id"]


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
        return flask.render_template(
            "questions.html",
            nav_data=NavData(),
            questions=questions,
            answers_dict=answers_date_dict
        )


class QuestionsView(QuestionsRangeView):
    def get_path(self) -> str:
        return "/questions/"
    
    def call(self, **kwargs):
        return super().call(start_date="earliest", end_date="latest")
