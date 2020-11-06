# Storium Frontend Web Service

This is the official repository of the [web
frontend](https://storium.cs.umass.edu) for the EMNLP 2020 long paper
*[STORIUM: A Dataset and Evaluation Platform for Machine-in-the-Loop Story
Generation](https://arxiv.org/abs/2010.01717)*.

## Python Package Naming

What is woolgatherer? It's a webservice that partakes in woolgathering, silly!
What exactly does that mean? The term woolgathering comes from people who
would literally gather tufts of wool that would get snagged as animals would
brush against a fence, tree, or other obstacle. By the mid-16th century the
term woolgathering took on the modern day connotation: a mind wandering
aimlessly, i.e. indulging in fanciful daydreaming. Thus it makes an apt name
for a web service designed to generate interesting topical suggestions for
story generation.

## Usage

There are are currently three environments: dev, stage, & prod. Run `make
build-dev` or `make build-prod` to create the docker containers to deploy the
service.

Afterward you can run `deploy-dev` or `make deploy-prod` to start the service.

## Setup

You can start a shell in the container using:

```
docker-compose -f build/dev/docker-compose.yml run backend sh
```

This needs to happen before deploying the service, so that you can create and
tables or do any migrations that might be needed. Within the shell you can run
`gw-createdb` create the database (if it does not already exist). If you
include the flag `-t`, like `gw-createdb -t` it will create the tables as well.
This is fine to do in dev, but you should not do this in production. In
production you should run _[alembic](https://alembic.sqlalchemy.org/)_
migrations.
