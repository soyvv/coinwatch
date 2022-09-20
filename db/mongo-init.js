db.createUser(
  {
    user: "coinwatch",
    pwd: "password",
    roles: [
      {
        role: "readWrite",
        db: "coinwatch"
      }
    ]
  }
);
db.createCollection('coinwatch_config');
db.coinwatch_config.insertOne(
  {
    symbols: ['BTCUSDT', 'ETHUSDT'],
    update_interval: 2,
    calc_window: 60
  }
);