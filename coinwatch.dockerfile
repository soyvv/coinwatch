FROM python:3.8

WORKDIR /app

COPY requirements.txt ./
#RUN pip install --no-cache-dir -r requirements.txt  -i http://pypi.douban.com/simple/  --trusted-host=pypi.douban.com/simple

RUN pip install --no-cache-dir -r requirements.txt

COPY . .