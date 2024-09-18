# syntax=docker/dockerfile:1
FROM python:3.10-alpine
WORKDIR /code
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "dsa_bloc_bot.py"]
