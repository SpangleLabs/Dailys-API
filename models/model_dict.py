from models.dream_night import DreamNight
from models.fa_data import FuraffinityData
from models.sleep_data import SleepData

MODEL_DICT = {
    "sleep": SleepData,
    "duolingo": None,
    "chores": None,
    "furaffinity": FuraffinityData,
    "dreams": DreamNight,
    "mood": None
}
