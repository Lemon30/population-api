FROM python:3.7-slim
WORKDIR /code
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENVIRONMENT=development
RUN apt-get update \
    && apt-get install -y --reinstall build-essential

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN apt-get purge -y --auto-remove build-essential

EXPOSE 5000
COPY . .
CMD ["flask", "run"]