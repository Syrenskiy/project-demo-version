# Dockerfile
FROM python:3.12

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PGSSLCERT /tmp/postgresql.crt

WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY config/ssl/rds-global-bundle.pem /etc/ssl/certs/rds-global-bundle.pem

RUN apt-get update && apt-get install -y wget
RUN wget https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh
RUN chmod +x wait-for-it.sh
RUN mkdir -p /app/logs && \
    chown -R www-data:www-data /app /app/logs && \
    chmod -R 775 /app /app/logs
RUN mkdir -p /root/.postgresql && \
    ln -s /etc/ssl/certs/rds-global-bundle.pem /root/.postgresql/postgresql.crt && \
    chmod 644 /etc/ssl/certs/rds-global-bundle.pem && \
    chmod 755 /root/.postgresql
CMD ["celery", "-A", "princesscastle", "worker", "--loglevel=info", "-P", "eventlet"]
