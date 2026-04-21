FROM python:3.12-slim

# System dependencies for PDF/fonts support
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    g++ \
    libffi-dev \
    fonts-dejavu-core \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create reports output directory
RUN mkdir -p /app/reports_output

# Copy DejaVu fonts for PDF Russian support
RUN mkdir -p /app/static/fonts && \
    cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf /app/static/fonts/ && \
    cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf /app/static/fonts/ || true

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
