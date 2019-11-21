from datetime import timedelta, date

import numpy


def format_colour(colour):
    return "rgb({}, {}, {})".format(*colour)


class ColourScale:
    YELLOW = (255, 255, 0)
    GREEN = (87, 187, 138)
    RED = (230, 124, 115)
    WHITE = (255, 255, 255)
    DANDELION = (255, 214, 102)
    GREY_UNKNOWN = (217, 217, 217)
    GREY_NOT_IN_USE = (183, 183, 183)

    def __init__(self, start_val, end_val, start_colour, end_colour):
        self.start_value = start_val
        self.end_value = end_val
        self.start_colour = start_colour
        self.end_colour = end_colour
        self.null_colour = "transparent"

    def get_colour_for_value(self, value):
        if value is None or not isinstance(value, (int, float, timedelta, date)):
            return self.null_colour
        if not isinstance(value, (timedelta, date)) and numpy.isnan(value):
            return format_colour(self.GREY_UNKNOWN)
        ratio = (value-self.start_value) / (self.end_value-self.start_value)
        colour = (
                self.start_colour[0] + ratio * (self.end_colour[0] - self.start_colour[0]),
                self.start_colour[1] + ratio * (self.end_colour[1] - self.start_colour[1]),
                self.start_colour[2] + ratio * (self.end_colour[2] - self.start_colour[2])
        )
        return format_colour((int(x) for x in colour))


class MidPointColourScale(ColourScale):
    def __init__(self, start_val, mid_val, end_val, start_colour, mid_colour, end_colour):
        super().__init__(start_val, end_val, start_colour, end_colour)
        self.mid_val = mid_val
        self.mid_colour = mid_colour
        self.low_scale = ColourScale(start_val, mid_val, start_colour, mid_colour)
        self.high_scale = ColourScale(mid_val, end_val, mid_colour, end_colour)

    def get_colour_for_value(self, value):
        if value is None:
            return self.null_colour
        if value > self.mid_val:
            return self.high_scale.get_colour_for_value(value)
        else:
            return self.low_scale.get_colour_for_value(value)
