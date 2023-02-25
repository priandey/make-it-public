FROM --platform=linux/amd64 python:3.8-slim-buster
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt requirements.txt

RUN python3 -m pip install -r requirements.txt
