FROM python:3.9.9-slim-bullseye

COPY requirements.txt requirements.txt
RUN apt update -y && \
    apt install -y ipmitool && \
    pip3 install -r ./requirements.txt

COPY . .
ENTRYPOINT ["python3", "falcon_ipmi_fan_driver.py"]