create database coinwatch;

\c coinwatch

create table coin_price (
  time timestamptz not null,
  symbol text not null,
  value double precision null
);

select create_hypertable('coin_price', 'time');


