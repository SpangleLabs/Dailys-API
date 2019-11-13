import base64
import datetime
from io import BytesIO

import dateutil
from PIL import Image, ImageDraw
from models import SleepData


class SleepDiaryImage:
    col_table_bg = (124, 124, 124)
    col_border = (0, 0, 0)
    col_text = (0, 0, 0)

    HOURS = 24

    def __init__(self, pix_per_hour=20, start_hour=18):
        self.pix_per_hour = pix_per_hour
        self.start_hour = start_hour
        table_width = pix_per_hour * self.HOURS
        self.im = Image.new("RGBA", (table_width, 100))

        self.draw = ImageDraw.Draw(self.im)
        self.draw.rectangle([(0, 30), (table_width, 70)], self.col_table_bg, self.col_border, 1)

        am_width, _ = self.draw.textsize("am")
        pm_width, _ = self.draw.textsize("pm")
        midnight_width, _ = self.draw.textsize("midnight")
        noon_width, _ = self.draw.textsize("noon")
        if start_hour > 12:
            self.draw.text((0, 0), "pm", self.col_text)
            midnight_x = ((24 - start_hour) * pix_per_hour) - midnight_width // 2
            self.draw.text((midnight_x, 0), "midnight", self.col_text)
            am_x = ((26 - start_hour) * pix_per_hour)
            self.draw.text((am_x, 0), "am", self.col_text)
            noon_x = ((36 - start_hour) * pix_per_hour) - noon_width // 2
            self.draw.text((noon_x, 0), "noon", self.col_text)
            self.draw.text((table_width - pm_width, 0), "pm", self.col_text)
        elif start_hour == 12:
            self.draw.text((0, 0), "noon", self.col_text)
            pm_x = (2 * pix_per_hour)
            self.draw.text((pm_x, 0), "pm", self.col_text)
            midnight_x = (12 * pix_per_hour) - midnight_width // 2
            self.draw.text((midnight_x, 0), "midnight", self.col_text)
            am_x = (14 * pix_per_hour)
            self.draw.text((am_x, 0), "am", self.col_text)
            self.draw.text((table_width - noon_width, 0), "noon", self.col_text)
        elif start_hour == 0:
            self.draw.text((0, 0), "midnight", self.col_text)
            am_x = midnight_width + pix_per_hour
            self.draw.text((am_x, 0), "am", self.col_text)
            noon_x = (12 * pix_per_hour) - noon_width // 2
            self.draw.text((noon_x, 0), "noon", self.col_text)
            pm_x = (14 * pix_per_hour)
            self.draw.text((pm_x, 0), "pm", self.col_text)
            self.draw.text((table_width - midnight_width, 0), "midnight", self.col_text)
        else:
            self.draw.text((0, 0), "am", self.col_text)
            noon_x = (12 - start_hour) * pix_per_hour - noon_width // 2
            self.draw.text((noon_x, 0), "noon", self.col_text)
            pm_x = (14 - start_hour) * pix_per_hour
            self.draw.text((pm_x, 0), "pm", self.col_text)
            midnight_x = (24 - start_hour) * pix_per_hour - midnight_width // 2
            self.draw.text((midnight_x, 0), "midnight", self.col_text)
            self.draw.text((table_width - am_width, 0), "am", self.col_text)

        for hour in range(self.HOURS + 1):
            line_x = hour * pix_per_hour
            if hour % 2 == 0:
                text = str(((hour + start_hour - 1) % 12) + 1)
                text_width, _ = self.draw.textsize(text)
                if hour == 0:
                    text_x = line_x
                elif hour == self.HOURS:
                    text_x = line_x - text_width
                else:
                    text_x = line_x - text_width // 2
                self.draw.text((text_x, 15), text, self.col_text)
            self.draw.line([(line_x, 30), (line_x, 70)], self.col_border)

    def add_sleep_data(self, sleep_data: SleepData):
        graph_date = dateutil.parser.parse(sleep_data.date)
        if sleep_data.interruptions is None:
            self._add_period(graph_date, sleep_data.sleep_time, sleep_data.wake_time)
        else:
            start_time = sleep_data.sleep_time
            for interruption in sleep_data.interruptions:
                end_time = interruption['wake_time']
                self._add_period(graph_date, start_time, end_time)
                start_time = interruption['sleep_time']
            end_time = sleep_data.wake_time
            self._add_period(graph_date, start_time, end_time)

    def _add_period(
            self,
            graph_date: datetime.date,
            start_time: datetime.datetime,
            end_time: datetime.datetime
    ):
        diary_start = datetime.datetime.combine(graph_date, datetime.time(self.start_hour))
        if self.start_hour > 12:
            diary_start -= datetime.timedelta(days=1)
        start_x = (start_time - diary_start).total_seconds()/3600*self.pix_per_hour
        end_x = (end_time - diary_start).total_seconds()/3600*self.pix_per_hour
        self.draw.line([(start_x, 40), (start_x, 60)], self.col_border)
        self.draw.line([(start_x, 50), (end_x, 50)], self.col_border)
        self.draw.line([(end_x, 40), (end_x, 60)], self.col_border)

    def save_to_file(self, filename):
        self.im.save(filename, "PNG")

    def to_base64_encoded(self):
        buffered = BytesIO()
        self.im.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue())
