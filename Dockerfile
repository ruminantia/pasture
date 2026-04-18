FROM python:3.11-slim

# Build arguments for user ID and group ID
ARG USER_ID=1000
ARG GROUP_ID=1000

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

# Create non-root user with matching UID/GID
RUN groupadd -g ${GROUP_ID} pasture && \
    useradd -u ${USER_ID} -g pasture -m -s /bin/bash pasture

WORKDIR /app

# Copy and install requirements as root first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create output directory and set ownership
RUN mkdir -p /app/output && \
    chown -R pasture:pasture /app

# Switch to non-root user
USER pasture

# Run the scraper in continuous mode
CMD ["python3", "src/main.py"]
