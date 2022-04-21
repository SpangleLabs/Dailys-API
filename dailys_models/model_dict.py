from dailys_models.dream_night import DreamNight
from dailys_models.fa_data import FuraffinityData
from dailys_models.mood_measurement import MoodDay
from dailys_models.questions import QuestionsDay
from dailys_models.sleep_data import SleepData

MODEL_DICT = {
    "chores": None,
    "dreams": DreamNight,
    "duolingo": None,
    "furaffinity": FuraffinityData,
    "mood": MoodDay,
    "questions": QuestionsDay,
    "sleep": SleepData,
    "sploo": None
}
