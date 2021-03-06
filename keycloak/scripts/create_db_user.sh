#!/bin/bash
set -e

POSTGRES="psql --username ${POSTGRES_USER}"

echo "Creating database role: ${KEYCLOAK_DB_USER}"

$POSTGRES <<EOSQL
CREATE USER ${KEYCLOAK_DB_USER} WITH CREATEDB PASSWORD '${KEYCLOAK_DB_PASS}';
EOSQL
