FROM mcr.microsoft.com/playwright/python:v1.58.0-noble

WORKDIR /app

COPY backend/requirements.txt /tmp/backend-requirements.txt
RUN pip install --no-cache-dir -r /tmp/backend-requirements.txt

# Configura as permissões para o usuário pwuser baixar o Chromium
ENV PLAYWRIGHT_BROWSERS_PATH=/home/pwuser/.cache/ms-playwright
RUN mkdir -p /home/pwuser/.cache/ms-playwright && chown -R pwuser:pwuser /home/pwuser

USER pwuser
RUN playwright install chromium
USER root

COPY . /app
RUN mkdir -p /tmp/notas_compensadas && chown -R pwuser:pwuser /app /tmp/notas_compensadas

USER pwuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    JOBS_BASE_DIR=/tmp/notas_compensadas \
    MIDAS_PLAYWRIGHT_RUNTIME_MODE=auto

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
