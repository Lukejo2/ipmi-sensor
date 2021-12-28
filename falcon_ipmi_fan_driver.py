import logging
import time
import traceback
import os
import subprocess
from dotenv import load_dotenv
from typing import List

load_dotenv()

DEFAULT_FAN_PERCENT = 10
FAN_STEP = 5
INTERVAL_SECONDS = int(os.getenv('INTERVAL', '60'))
IPMI_HOST = os.getenv('IPMI_HOST')
IPMI_USERNAME = os.getenv('IPMI_USERNAME')
IPMI_PASSWORD = os.getenv('IPMI_PASSWORD')

MAX_PERCENT = int(os.getenv('MAX_PERCENT', '50'))
CPU_THRESHOLD = int(os.getenv('CPU_THRESHOLD', '65'))


def main():
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        level=logging.NOTSET
    )
    logging.info(
        f'Starting IPMI Fan driver with \n'
        f'Default percent: {10}%\n'
        f'Percent Step: {FAN_STEP}%\n'
        f'Threshold: {CPU_THRESHOLD}\n'
        f'Check Interval: {INTERVAL_SECONDS} seconds'
    )

    active_percent = DEFAULT_FAN_PERCENT
    logging.info(f'Setting starting fan percent to {DEFAULT_FAN_PERCENT}%')
    set_falcon_fan_percent(active_percent)
    while True:
        try:
            time.sleep(INTERVAL_SECONDS)
            events = get_sensor_events()
            cpu_temp = next((x for x in events if x['name'] == 'CPU_Diode_Temp'))
            value = int(float(cpu_temp['value']))
            unit = cpu_temp['unit']
            if value > CPU_THRESHOLD and active_percent < MAX_PERCENT:
                active_percent += FAN_STEP
                active_percent = min(active_percent, MAX_PERCENT)
                logging.warning(f'CPU temp is {value} {unit}. Setting fan percent to {active_percent}%.')
                set_falcon_fan_percent(active_percent)
                continue
            if value < CPU_THRESHOLD and active_percent > DEFAULT_FAN_PERCENT:
                active_percent = DEFAULT_FAN_PERCENT
                logging.info(f'CPU temp is {value} {unit}. Setting fan percent to {active_percent}%.')
                continue

            logging.info(f'CPU temp is {value} {unit}.')
        except Exception as e:
            logging.error(
                f'Exception! '
                f'Details: {str(e)} '
                f'Traceback: {traceback.format_exc()} '
            )


def ipmi_sensor(
    *,
    host: str = None,
    username: str = None,
    password: str = None,
    timeout: int = 120
) -> str:
    """
    Calls command ipmitool sensor

    :param host: Defaults to env IPMI_HOST
    :param username: Defaults to env IPMI_USERNAME
    :param password: Defaults to env IPMI_PASSWORD
    :param timeout: Command timeout in seconds
    :return: Output text from the command
    """
    host = host if host else IPMI_HOST
    username = username if username else IPMI_USERNAME
    password = password if password else IPMI_PASSWORD

    if not host:
        raise ValueError('Host is required!')
    if not username:
        raise ValueError('Username is required!')
    if not password:
        raise ValueError('Password is required!')

    env = os.environ.copy()
    env['IPMI_PASSWORD'] = password
    output: bytes = subprocess.check_output(
        ['ipmitool', '-I', 'lanplus', '-H', host, '-U', username, '-E', 'sensor'],
        env=env,
        timeout=timeout,
        stdin=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return output.decode('utf-8', errors='replace')


def ipmi_set_falcon_fan_percent(
    fan: int,
    percent: int,
    *,
    host: str = None,
    username: str = None,
    password: str = None,
    timeout: int = 30
):
    host = host if host else IPMI_HOST
    username = username if username else IPMI_USERNAME
    password = password if password else IPMI_PASSWORD

    if not host:
        raise ValueError('Host is required!')
    if not username:
        raise ValueError('Username is required!')
    if not password:
        raise ValueError('Password is required!')
    if fan not in range(2, 7):
        raise ValueError('Fan must be between 2 and 7')
    if percent not in range(0, 100):
        raise ValueError('Percent must be between 0 and 100')

    env = os.environ.copy()
    env['IPMI_PASSWORD'] = password
    subprocess.check_call(
        ['ipmitool', '-I', 'lanplus', '-H', host, '-U', username, '-E', 'raw', '0x3c', '0x14', str(fan), str(percent)],
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout
    )


def set_falcon_fan_percent(
    percent: int,
    *,
    host: str = None,
    username: str = None,
    password: str = None,
    timeout: int = 30
):
    for i in range(2, 7):
        ipmi_set_falcon_fan_percent(
            i,
            percent,
            host=host,
            username=username,
            password=password,
            timeout=timeout
        )


def get_sensor_events() -> List[dict]:
    output = ipmi_sensor()
    events = []
    for line in output.splitlines():
        line = line.strip()
        name, value, unit, \
            status, lower_non_recoverable, lower_critical, \
            lower_non_critical, upper_non_critical, \
            upper_critical, upper_non_recoverable = line.split('|')
        events.append({
            'name': name.strip(),
            'value': value.strip(),
            'unit': unit.strip(),
            'status': status.strip(),
            'lower_non_recoverable': lower_non_recoverable.strip(),
            'lower_critical': lower_critical.strip(),
            'lower_non_critical': lower_non_critical.strip(),
            'upper_non_critical': upper_non_critical.strip(),
            'upper_critical': upper_critical.strip(),
            'upper_non_recoverable': upper_non_recoverable.strip()
        })
    return events


if __name__ == '__main__':
    main()
