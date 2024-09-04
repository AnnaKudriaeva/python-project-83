#!/usr/bin/env bash

source .env
make install && psql -a -d $DATABASE_URL -f database.sql