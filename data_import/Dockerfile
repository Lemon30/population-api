FROM python:3.7-slim
RUN apt-get update \
    && apt-get install -y --reinstall build-essential

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN apt-get purge -y --auto-remove build-essential

COPY . .
ENTRYPOINT ["python", "main.py"]