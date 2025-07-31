FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libappindicator1 \
    libasound2 \
    libxshmfence1 \
    fonts-liberation \
    libgbm1 \
    xdg-utils \
    chromium \
    && apt-get clean

ENV PYTHONUNBUFFERED=1 \
    CHROME_BIN=/usr/bin/chromium

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN pip install chromedriver-autoinstaller

CMD ["python", "bot.py"]
