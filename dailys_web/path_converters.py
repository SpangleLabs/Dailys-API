import json
from datetime import datetime
from werkzeug.routing import BaseConverter, ValidationError

with open(__file__ + "/../named-dates.json", "r") as f:
    data = json.load(f)
    NAMED_DATES = {k: datetime.strptime(v, '%Y-%m-%d').date() for k, v in data.items()}


class DateConverter(BaseConverter):
    """Extracts a ISO8601 date from the path and validates it."""

    regex = r'\d{4}-\d{2}-\d{2}'

    def to_python(self, value):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError()

    def to_url(self, value):
        return value.strftime('%Y-%m-%d')


class StartDateConverter(DateConverter):
    """Extracts an ISO8601 date from the path and validates it, allowing 'earliest'."""

    regex = DateConverter.regex + "|earliest" + "".join(["|"+x for x in NAMED_DATES.keys()])

    def to_python(self, value):
        if value.lower() == "earliest":
            return "earliest"
        elif value.lower() in NAMED_DATES:
            return NAMED_DATES[value.lower()]
        else:
            return super().to_python(value)

    def to_url(self, value):
        return "earliest" if value == "earliest" else super().to_url(value)


class EndDateConverter(DateConverter):
    """Extracts an ISO8601 date from the path and validates it, allowing 'latest'."""

    regex = DateConverter.regex + "|latest" + "".join(["|"+x for x in NAMED_DATES.keys()])

    def to_python(self, value):
        if value.lower() == "latest":
            return "latest"
        elif value.lower() in NAMED_DATES:
            return NAMED_DATES[value.lower()]
        else:
            return super().to_python(value)

    def to_url(self, value):
        return "latest" if value == "latest" else super().to_url(value)


class SpecifiedDayConverter(EndDateConverter):
    """Extracts ISO8601 date from path and validates, allowing 'latest' and 'static'."""

    regex = EndDateConverter.regex + "|static"

    def to_python(self, value):
        if value.lower() == "static":
            return "static"
        else:
            return super().to_python(value)

    def to_url(self, value):
        return "static" if value == "static" else super().to_url(value)
