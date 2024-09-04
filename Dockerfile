FROM python:3.11-slim-bookworm

RUN apt update && \
    export DEBIAN_FRONTEND=noninteractive && \ 
    apt install -y --no-install-recommends git curl

WORKDIR /opt/app

RUN mkdir -p -m=777 ailurus/.adce_data
COPY .env.example .env
COPY . .

RUN pip install .
RUN for folder in /opt/app/ailurus/svcmodes/*/; do \
        if [ -f "$folder/requirements.txt" ]; then \
            pip3 install -r "$folder/requirements.txt"; \
        fi \
    done

RUN chmod +x startup.sh
RUN ln -s /run/shm /dev/shm
    
EXPOSE 5000

ENTRYPOINT [ "./startup.sh" ]