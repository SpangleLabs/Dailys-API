import base64
import datetime
from io import BytesIO

import dateutil
from PIL import Image, ImageDraw

from dailys_models.sleep_data import SleepData


class SleepDiaryImage:
    col_table_bg = (124, 124, 124)
    col_border = (50, 50, 50)
    col_data = (0, 0, 0)
    col_text = (0, 0, 0)
    
    box_top_y = 22
    box_bottom_y = 42
    img_height = 52

    HOURS = 24

    def __init__(self, pix_per_hour=20, start_hour=18):
        self.pix_per_hour = pix_per_hour
        self.start_hour = start_hour
        self.table_width = pix_per_hour * self.HOURS
        self.im = Image.new("RGBA", (self.table_width, self.img_height))

        self.draw = ImageDraw.Draw(self.im)
        self.draw.rectangle(
            [(0, self.box_top_y), (self.table_width, self.box_bottom_y)], self.col_table_bg, self.col_border, 1
        )
        self._draw_labels()
        self._draw_hours()

    def _draw_labels(self):
        label_y = -1
        am_width = self.draw.textlength("am")
        pm_width = self.draw.textlength("pm")
        midnight_width = self.draw.textlength("midnight")
        noon_width = self.draw.textlength("noon")
        if self.start_hour > 12:
            self.draw.text((0, label_y), "pm", self.col_text)
            midnight_x = ((24 - self.start_hour) * self.pix_per_hour) - midnight_width // 2
            self.draw.text((midnight_x, label_y), "midnight", self.col_text)
            am_x = ((26 - self.start_hour) * self.pix_per_hour)
            self.draw.text((am_x, label_y), "am", self.col_text)
            noon_x = ((36 - self.start_hour) * self.pix_per_hour) - noon_width // 2
            self.draw.text((noon_x, label_y), "noon", self.col_text)
            self.draw.text((self.table_width - pm_width, label_y), "pm", self.col_text)
        elif self.start_hour == 12:
            self.draw.text((0, label_y), "noon", self.col_text)
            pm_x = (2 * self.pix_per_hour)
            self.draw.text((pm_x, label_y), "pm", self.col_text)
            midnight_x = (12 * self.pix_per_hour) - midnight_width // 2
            self.draw.text((midnight_x, label_y), "midnight", self.col_text)
            am_x = (14 * self.pix_per_hour)
            self.draw.text((am_x, label_y), "am", self.col_text)
            self.draw.text((self.table_width - noon_width, label_y), "noon", self.col_text)
        elif self.start_hour == 0:
            self.draw.text((0, label_y), "midnight", self.col_text)
            am_x = midnight_width + self.pix_per_hour
            self.draw.text((am_x, label_y), "am", self.col_text)
            noon_x = (12 * self.pix_per_hour) - noon_width // 2
            self.draw.text((noon_x, label_y), "noon", self.col_text)
            pm_x = (14 * self.pix_per_hour)
            self.draw.text((pm_x, label_y), "pm", self.col_text)
            self.draw.text((self.table_width - midnight_width, label_y), "midnight", self.col_text)
        else:
            self.draw.text((0, label_y), "am", self.col_text)
            noon_x = (12 - self.start_hour) * self.pix_per_hour - noon_width // 2
            self.draw.text((noon_x, label_y), "noon", self.col_text)
            pm_x = (14 - self.start_hour) * self.pix_per_hour
            self.draw.text((pm_x, label_y), "pm", self.col_text)
            midnight_x = (24 - self.start_hour) * self.pix_per_hour - midnight_width // 2
            self.draw.text((midnight_x, label_y), "midnight", self.col_text)
            self.draw.text((self.table_width - am_width, label_y), "am", self.col_text)

    def _draw_hours(self):
        hours_y = 10
        for hour in range(self.HOURS + 1):
            line_x = hour * self.pix_per_hour
            if hour % 2 == 0:
                text = str(((hour + self.start_hour - 1) % 12) + 1)
                text_width = self.draw.textlength(text)
                if hour == 0:
                    text_x = line_x
                elif hour == self.HOURS:
                    text_x = line_x - text_width
                else:
                    text_x = line_x - text_width // 2
                self.draw.text((text_x, hours_y), text, self.col_text)
            self.draw.line([(line_x, self.box_top_y), (line_x, self.box_bottom_y)], self.col_border)

    def add_sleep_data(self, sleep_data: SleepData):
        graph_date = sleep_data.date.date()
        if sleep_data.interruptions is None:
            self._add_period(graph_date, sleep_data.sleep_time, sleep_data.wake_time)
        else:
            start_time = sleep_data.sleep_time
            for interruption in sleep_data.interruptions:
                if "wake_time" and "sleep_time" in interruption:
                    end_time = dateutil.parser.parse(interruption['wake_time'])
                    self._add_period(graph_date, start_time, end_time)
                    start_time = dateutil.parser.parse(interruption['sleep_time'])
            end_time = sleep_data.wake_time
            self._add_period(graph_date, start_time, end_time)
        # Add sleeping time
        self._add_sleeping_time(sleep_data.time_sleeping)

    def _add_period(
            self,
            graph_date: datetime.date,
            start_time: datetime.datetime,
            end_time: datetime.datetime
    ):
        flare_height = 10
        diary_start = datetime.datetime.combine(graph_date, datetime.time(self.start_hour), tzinfo=start_time.tzinfo)
        start_x = (start_time - diary_start).total_seconds()/3600*self.pix_per_hour
        end_x = (end_time - diary_start).total_seconds()/3600*self.pix_per_hour
        mid_y = (self.box_bottom_y + self.box_top_y) // 2
        self.draw.line([(start_x, mid_y - flare_height), (start_x, mid_y + flare_height)], self.col_data, 3)
        self.draw.line([(start_x, mid_y), (end_x, mid_y)], self.col_data, 3)
        self.draw.line([(end_x, mid_y - flare_height), (end_x, mid_y + flare_height)], self.col_data, 3)

    def _add_sleeping_time(self, time_sleeping: datetime.timedelta):
        hours = time_sleeping.seconds//3600
        minutes = (time_sleeping.seconds - hours * 3600)//60
        text = f"TOTAL SLEEP TIME: {hours}h {minutes:02}m"
        text_width = self.draw.textlength(text)
        self.draw.text((self.table_width-text_width, self.box_bottom_y), text, self.col_text)

    def save_to_file(self, filename):
        self.im.save(filename, "PNG")

    def to_base64_encoded(self):
        buffered = BytesIO()
        self.im.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('ascii')
