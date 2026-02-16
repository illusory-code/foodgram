FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .
COPY /ent_point.prod.sh /ent_point.prod.sh
RUN chmod +x /ent_point.prod.sh
ENTRYPOINT ["/ent_point.prod.sh"]

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram_backend.wsgi"]
