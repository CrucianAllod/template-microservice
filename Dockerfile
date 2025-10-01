FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y curl wget && \
    pip install uv


RUN mkdir -p ~/.postgresql && \
    wget "https://storage.yandexcloud.net/cloud-certs/CA.pem" \
        --output-document ~/.postgresql/root.crt && \
    chmod 0600 ~/.postgresql/root.crt && \
    apt-get remove -y wget && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY src ./src

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev --compile-bytecode

COPY README.md start.sh start-dev.sh ./

RUN chmod +x start.sh && chmod +x start-dev.sh

EXPOSE 8000

CMD [ "/bin/bash", "start.sh" ]