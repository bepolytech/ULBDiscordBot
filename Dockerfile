FROM python:3
# use python:3.11.0rc2-slim for less vulnerabilities ? (from `docker scan`)

WORKDIR /usr/src/ulbdiscordbot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]
