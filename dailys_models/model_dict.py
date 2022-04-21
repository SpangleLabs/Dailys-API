from dailys_models.dream_night import DreamNight
from dailys_models.fa_data import FuraffinityData
from dailys_models.sleep_data import SleepData
from dailys_models.questions import QuestionsDay

MODEL_DICT = {
    "sleep": SleepData,
    "duolingo": None,
    "chores": None,
    "furaffinity": FuraffinityData,
    "dreams": DreamNight,
    "mood": None,
    "questions": QuestionsDay
}
