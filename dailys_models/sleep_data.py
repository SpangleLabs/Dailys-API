import dateutil.parser

from dailys_models.models import Data


class SleepData(Data):

    def __init__(self, json_data):
        super().__init__(json_data)
        try:
            self.sleep_time = dateutil.parser.parse(json_data['data']['sleep_time'])
            self.wake_time = dateutil.parser.parse(json_data['data']['wake_time'])
            self.time_sleeping = self.wake_time - self.sleep_time
            self.interruptions = json_data['data'].get('interruptions')
            self.interruptions_text = ""
            if self.interruptions is not None:
                self.interruptions_text = self.format_interruptions()
        except KeyError:
            raise KeyError("Sleep data missing a wake or sleep time on {}".format(json_data['date']))

    def format_interruptions(self):
        return "{} interruption{} ({})".format(
            len(self.interruptions),
            "" if len(self.interruptions) == 1 else "s",
            ", ".join([self.format_interruption(x) for x in self.interruptions])
        )

    def format_interruption(self, interrupt):
        if "wake_time" and "sleep_time" in interrupt:
            start = dateutil.parser.parse(interrupt['wake_time'])
            end = dateutil.parser.parse(interrupt['sleep_time'])
            period = end - start
            return "{} minutes ({} - {})".format(int(period.total_seconds() // 60), start.time(), end.time())
        elif "notes" in interrupt:
            return interrupt['notes']
        else:
            return "Unknown interruption"
    
    def format_sleep_time(self, timezone):
        return self.sleep_time.astimezone(timezone).strftime("%H:%M:%S")

    def format_wake_time(self, timezone):
        return self.wake_time.astimezone(timezone).strftime("%H:%M:%S")
    
    def format_time_sleeping(self):
        hours, seconds = divmod(self.time_sleeping.total_seconds(), 3600)
        minutes, seconds = divmod(seconds, 60)
        return f"{hours:.0f}h {minutes:.0f}m {seconds:.0f}s"
    
    def value_count(self) -> int:
        return sum(int(bool(x)) for x in [self.sleep_time, self.wake_time, self.interruptions])
