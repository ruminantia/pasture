FROM python:3.11-slim

# Install Firefox and timezone data
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set Firefox binary location
ENV FIREFOX_BIN=/usr/bin/firefox

# Set timezone (can be overridden in docker-compose.yml)
ENV TZ=America/Phoenix

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the scraper in continuous mode
CMD ["python3", "src/main.py"]
