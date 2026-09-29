FROM python:3.11

COPY . .
RUN pip install -r requirements.txt

ENV FLASK_APP="main.py"
ENTRYPOINT ["flask", "run", "--host", "0.0.0.0"]
