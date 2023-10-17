import subprocess

from common.constants import Service, ServiceAction


def get_services() -> list[str]:
    return [service for service in Service]


def control_service(action: ServiceAction, service: Service) -> bool | None:
    command = ["sudo", "systemctl", "--no-block", action.value, service.value]
    result = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if action == ServiceAction.STATUS:
        return "active (running)" in result.stdout.decode("utf-8")
    
    return None


def control_services(action: ServiceAction) -> None:
    for service in get_services():
        control_service(action, service)
