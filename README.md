## CoinWatch


A simple web app built with:
 * streamlib
 * zerorpc
 * mongodb(as config db) and timescaledb(as timeseries db)


### Build & Run

To start the app
```shell
docker-compose up
```
once started, the dashboard is served on port 8051. 


To re-build the images:
```shell
docker-compose build
```


To change config, edit the /db/mongo-init.js.