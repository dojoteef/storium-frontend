FROM python:3.7-alpine
WORKDIR /var/www/woolgatherer
COPY setup.py .
COPY src src
COPY scripts scripts
RUN apk add --no-cache --virtual .build-deps gcc libc-dev postgresql-dev make \
      && pip install .[all] && apk del .build-deps gcc libc-dev postgresql-dev make \
      && rm -rf setup.py src

CMD gw
