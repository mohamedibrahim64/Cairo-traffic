FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p data/processed models

# Expose port for the Flask app
EXPOSE 5000

# Set environment variables
ENV PYTHONPATH=/app/src
# Run the application
CMD ["python", "src/web/app.py"]