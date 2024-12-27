FROM python:3.10.7

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN pip install playwright
RUN playwright install
RUN playwright install-deps

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "-b", "0.0.0.0:8000", "app:app"]