FROM python:3.11-slim-bookworm

RUN apt update && \
    export DEBIAN_FRONTEND=noninteractive && \ 
    apt install -y --no-install-recommends git curl

WORKDIR /opt/app

# Workaround for python module installation error
RUN mkdir and_platform && touch and_platform/__init__.py && touch README.md
COPY pyproject.toml .
RUN pip install .

RUN mkdir -p -m=777 and_platform/.adce_data
COPY .env.example .env
COPY . .
RUN chmod +x startup.sh
RUN ln -s /run/shm /dev/shm

EXPOSE 5000

ENTRYPOINT [ "./startup.sh" ]