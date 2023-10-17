import subprocess

from common.constants import Service, ServiceAction


def get_services() -> list[str]:
    return [service for service in Service]


def control_service(action: ServiceAction, service: Service) -> bool | None:
    command = ["sudo", "systemctl", "--no-block", action.value, service.value]
    result = subprocess.run(command, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                            universal_newlines=True)
    
    if action == ServiceAction.STATUS:
        return "active (running)" in result.stdout
    
    return None


def control_services(action: ServiceAction) -> None:
    for service in get_services():
        control_service(action, service)


def ping(ip: str):
    """Returns True if host responds to a ping request on Ubuntu."""
    command = ["ping", "-c", "1", ip]

    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
        return True
    except subprocess.CalledProcessError:
        return False
