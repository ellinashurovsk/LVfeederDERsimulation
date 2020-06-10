FROM python:3.8.3-slim

RUN apt-get update && \
    apt-get install -y build-essential git liblapack-dev libblas-dev

# specific versions that are guaranteed to work with the code
RUN pip install wheel==0.34.2 numba==0.49.1 pandas==1.0.4 cvxpy==1.0.31

# latest commit on branch 'develop' as of 2020.06.09
RUN pip install git+https://github.com/e2nIEE/pandapower.git@1e6f29d632a31acf437d094b69edcefc048dbcfe

WORKDIR /app

COPY docker/entrypoint.sh entrypoint.sh
COPY simulation.py simulation.py

ENTRYPOINT ["./entrypoint.sh"]
