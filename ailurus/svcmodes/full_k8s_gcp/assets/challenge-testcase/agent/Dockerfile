FROM python:3.12-alpine

WORKDIR /opt/agentchecker

RUN mkdir -p /configmap/flag && touch /configmap/flag/flag.txt && touch /configmap/.service_secret

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

CMD ["python", "main.py"]