FROM python:3.13-slim

# Install Playwright system dependencies
RUN apt-get update && apt-get install -y \
    wget gnupg \
    libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libasound2 libxss1 libxrandr2 libgconf-2-4 \
    fonts-liberation libappindicator3-1 libasound2 \
    libatk-bridge2.0-0 libcairo-gobject2 libgtk-3-0 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt && \
    python -m playwright install --with-deps chromium

# Render detects port 10000 automatically
EXPOSE 10000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
