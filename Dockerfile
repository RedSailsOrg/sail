FROM python:3-alpine
RUN apk add rsvg-convert imagemagick
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /src/
WORKDIR /src/
