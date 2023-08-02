FROM python:3.11-alpine3.18
WORKDIR /cdg_bot/
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY ./app .
CMD python EnglishPolicemanBot.py
