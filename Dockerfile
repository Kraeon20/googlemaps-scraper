FROM python:3.10.7-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    libnss3 libatk1.0 libpangocairo-1.0-0 libxcomposite1 libxrandr2 \
    libxdamage1 libxkbcommon0 libgtk-3-0 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its dependencies
RUN pip install playwright
RUN playwright install
RUN playwright install-deps

# Copy project files
COPY . .

EXPOSE 8000

# Use Uvicorn for production
CMD ["python", "app.py"]