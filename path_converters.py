from datetime import datetime
from werkzeug.routing import BaseConverter, ValidationError


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


class EndDateConverter(DateConverter):
    """Extracts an ISO8601 date from the path and validates it, allowing 'latest'."""

    regex = DateConverter.regex + "|latest"

    def to_python(self, value):
        if value.lower() == "latest":
            return "latest"
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
