import flask

from dailys_models.questions import QuestionsDay, StaticQuestion
from dailys_web.blueprints.views.base_view import View
from dailys_web.nav_data import NavData


class IndividualQuestionRangeView(View):
    def get_path(self) -> str:
        return "/questions/<question_id>/<start_date:start_date>/<end_date:end_date>/"
  
    def call(self, **kwargs):
        question_id = kwargs["question_id"]
        start_date = kwargs["start_date"]
        end_date = kwargs["end_date"]
        # Get question data
        q_static = self.data_source.get_entries_for_stat_on_date("questions", "static")[0]['data']
        questions = [StaticQuestion(data) for data in q_static["questions"]]
        question = next((question for question in questions if question.id == question_id), None)
        # Get answers data
        answers_data = self.data_source.get_entries_for_stat_over_range("questions", start_date, end_date)
        answers_days = [QuestionsDay(data) for data in answers_data]
        answers_days = [answers for answers in answers_days if question_id in answers.answers]
        # Get stats object
        return flask.render_template(
            "question_each.html",
            question=question,
            start_date=start_date,
            end_date=end_date,
            answers_days=answers_days
        )


class IndividualQuestionView(IndividualQuestionRangeView):
    def get_path(self) -> str:
        return "/questions/<question_id>/"
    
    def call(self, **kwargs):
        return super().call(start_date="earliest", end_date="latest", question_id=kwargs["question_id"])
