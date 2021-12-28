FROM python:3.9.9-slim-bullseye

COPY requirements.txt requirements.txt
RUN apt --no-cache update -y && \
    apt --no-cache install ipmitool && \
    pip3 --no-cahce install -r ./requirements.txt

COPY . .
ENTRYPOINT ["python3", "falcon_ipmi_fan_driver.py"]