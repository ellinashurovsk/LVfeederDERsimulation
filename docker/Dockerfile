FROM python:3.8.3-slim

RUN apt-get update && \
    apt-get install -y build-essential git liblapack-dev libblas-dev

RUN python3 --version
RUN pip3 --version

COPY requirements.txt requirements.txt

# specific versions that are guaranteed to work with the code
RUN pip3 install -r requirements.txt

WORKDIR /app

COPY docker/entrypoint.sh entrypoint.sh
COPY simulation.py simulation.py

ENTRYPOINT ["./entrypoint.sh"]
