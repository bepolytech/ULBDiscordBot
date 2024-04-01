#FROM python:3 # use alpine for reduced size
FROM python:3.11.8-alpine

WORKDIR /usr/src/ulbdiscordbot

RUN python3 -m pip install --upgrade pip

COPY requirements.txt ./
RUN pip3 install --extra-index-url https://alpine-wheels.github.io/index --no-cache-dir -r requirements.txt # if wheels dependencies build errors when using alpine
#RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]
