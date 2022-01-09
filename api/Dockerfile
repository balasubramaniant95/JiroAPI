FROM python:3
LABEL MAINTAINER = "Balasubramanian Thiruvenkatesan <balasubramaniant.9507@gmail.com>"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
WORKDIR /app

CMD [ "gunicorn", "--config", "gunicorn.conf.py", "app:app"]
