FROM python:3.11-slim

# Install Firefox
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set Firefox binary location
ENV FIREFOX_BIN=/usr/bin/firefox

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "src/main.py"]
