FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh
#RUN chmod +x /app/renew_token.sh

RUN useradd -ms /bin/bash odinuser && chown -R odinuser:odinuser /app
USER odinuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python3", "main.py"]