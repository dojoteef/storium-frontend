# Woolgatherer Web Service

What exactly is woolgatherer? It's a webservice that partakes in woolgathering!
What exactly does that mean? Well, the term woolgather comes from people who
would literally gather tufts of wool that would get snagged as animals would
brush against a fence, tree, or other obstacle. By the mid-16th century the
term woolgathering took on the modern day connotation: a mind wandering
aimlessly, i.e. indulding in fanciful daydreaming. The service is designed to
generate interesting topical suggestions for where to take a story next.


## Usage

There are are currently three environments: dev, stage, & prod. Run `make
build-dev` or `make build-prod` to create the docker containers to deploy the
service.

Afterward you can run `deploy-dev` or `make deploy-prod` to start the service.


## Setup

You can start a shall in the container using:

```
docker-compose -f build/dev/docker-compose.yml run backend sh
```

This needs to happen before deploying the service, so that you can create and
tables or do any migrations that might be needed. Within the shell you can run
`gw-createdb` create the database (if it does not already exist). If you
include the flag `-t`, like `gw-createdb -t` it will create the tables as well.
This is fine to do in dev, but you should not do this in production. In
production you should run _alembic_ migrations.
