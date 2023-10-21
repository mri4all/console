import subprocess

import common.logger as logger

log = logger.get_logger()

from common.constants import Service, ServiceAction


def get_services() -> list[Service]:
    return [service for service in Service]


def control_service(action: ServiceAction, service: Service) -> bool | None:
    command = ["sudo", "systemctl", "--no-block", action.value, service.value]
    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    if action == ServiceAction.STATUS:
        # Service is not installed
        if result.returncode == 4:
            return False
        return "active (running)" in result.stdout
    else:
        if result.returncode != 0:
            log.warning(f"Failed to {action.value} {service.value}")
            log.warning(f"Reason: {result.stderr}")
    return None


def control_services(action: ServiceAction) -> None:
    for service in get_services():
        control_service(action, service)


def ping(ip: str):
    """Returns True if host responds to a ping request on Ubuntu."""
    command = ["ping", "-w", "1", "-c", "1", ip]
    log.info(f"Trying to ping device: {' '.join(command)}")
    try:
        subprocess.check_output(
            command, stderr=subprocess.STDOUT, universal_newlines=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def restart_device():
    log.info("Hard reset of acquisition device requested")
    # TODO
    return True


def run_device_bootsequence() -> bool:
    # TODO
    return True


def run_device_test() -> bool:
    # TODO
    return True
