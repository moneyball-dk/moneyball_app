# Base img
FROM python:3


# Add essentials
# RUN apk add --no-cache postgresql-libs
# RUN apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev zlib-dev
# RUN apk --update add libxml2-dev libxslt-dev libffi-dev gcc musl-dev libgcc curl
# RUN apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev
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
#CMD ["gunicorn", "-b", ":5000", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
#ENTRYPOINT ["./boot.sh"]
