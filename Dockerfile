FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh

RUN useradd -ms /bin/bash odinuser && chown -R odinuser:odinuser /app
USER odinuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python3", "main.py"]