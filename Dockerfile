FROM python:3.7-alpine

ARG PIP_CMD="pip install"

# Copy the files needed to build the app
WORKDIR /var/www/woolgatherer
COPY setup.py alembic.ini ./
COPY src src
COPY sql sql
COPY alembic alembic
COPY scripts scripts
COPY static static
COPY templates templates

# Install build dependencies, then install app, then remove build dependencies
# and install the libpq dependency for postgresql
RUN apk add --no-cache --virtual .build-deps gcc libc-dev postgresql-dev make \
      && $PIP_CMD .[postgresql] && apk del .build-deps gcc libc-dev make \
      && rm -rf setup.py alembic.ini src alembic scripts && apk add --no-cache libpq \
      && ln -s /usr/local/share/woolgatherer/alembic.ini . \
      && ln -s /usr/local/share/woolgatherer/alembic .

# Create a user and group that actually run the app, so we aren't running as root
RUN addgroup -S gw && mkdir /home/gw && adduser -S gw -G gw -h /home/gw \
      && chown gw:gw /home/gw

# Tell docker that all future commands should run as the gw user
USER gw
CMD gw
