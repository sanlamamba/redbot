FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Web dashboard port (only exposed when --web flag is passed)
EXPOSE 8080

# Migrations run automatically at startup via Database.__init__().
# Use CMD with shell form so WEB and WEB_PORT env vars can be interpolated.
CMD python main.py ${WEB:+--web} ${WEB_PORT:+--web-port $WEB_PORT}
