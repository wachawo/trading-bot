# Stage 1: Builder - Install dependencies
FROM python:3.9-slim AS builder

WORKDIR /app

# Install build dependencies
RUN pip install --upgrade pip

# Copy requirements and install packages
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir=/app/wheels -r requirements.txt

# Stage 2: Final Image - No internet access needed
FROM python:3.9-slim

WORKDIR /app

# Copy pre-installed packages from the builder stage
COPY --from=builder /app/wheels /wheels

# Install packages from local wheels without needing internet
RUN pip install --no-index --find-links=/wheels /wheels/*

# Copy the application source code
COPY src/ ./src/
COPY data/ ./data/
COPY .env .

# Set the command to run the application
CMD ["python", "-u", "src/main.py"]
