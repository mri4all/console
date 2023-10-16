import asyncio
from common.constants import Service, ServiceAction


async def async_run(cmd, **params) -> (int | None, bytes, bytes):
    """Executes the given shell command in a way compatible with asyncio."""
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, **params
    )

    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout, stderr


def get_services() -> list[str]:
    return [service.value for service in Service]


async def control_services(action: ServiceAction) -> None:
    services = get_services()
    for service in services:
        command = "sudo systemctl " + action.value + " " + service
        await async_run(command)
