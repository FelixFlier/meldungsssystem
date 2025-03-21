FROM python:3.9-slim

WORKDIR /app

# Systemabhängigkeiten installieren
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Chrome für Selenium installieren
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Stellen sicher, dass Verzeichnisse existieren
RUN mkdir -p /app/logs /app/static

# Python-Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Umgebungsvariablen setzen
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app:${PATH}" \
    PYTHONPATH="/app:${PYTHONPATH}"

# Einfachen Gesundheitscheck-Endpunkt hinzufügen
RUN echo -e 'from fastapi import FastAPI\n\n@app.get("/health")\ndef health_check():\n    return {"status": "ok"}' >> health_check.py

# Exponieren des Ports
EXPOSE 8000

# Starten mit Gunicorn in Produktion
CMD exec gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 main:app