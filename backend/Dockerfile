FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5002

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip setuptools wheel
RUN pip install -r /app/requirements.txt

# Copy application code
COPY . /app

# Expose port and provide a sensible default command using gunicorn
EXPOSE ${PORT}

CMD ["gunicorn", "-w", "4", "-k", "gthread", "-b", "0.0.0.0:5002", "app:app"]
