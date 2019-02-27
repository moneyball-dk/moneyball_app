# Base img
FROM python:3


# Python installs
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install numpy
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn pymysql

COPY app app
COPY migrations migrations
COPY config.py moneyball.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP moneyball.py

EXPOSE 5000
CMD ["./boot.sh"]
#ENTRYPOINT ["./boot.sh"]
