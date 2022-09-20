FROM timescale/timescaledb:latest-pg14
COPY ./db/coinwatch.sql /docker-entrypoint-initdb.d/
