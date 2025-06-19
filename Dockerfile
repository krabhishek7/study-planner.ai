# Production Dockerfile for Study Planner.AI
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Railway provides the PORT environment variable
# We don't need to EXPOSE it since Railway handles this automatically

# Use gunicorn for production with dynamic port binding
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 run:app 
