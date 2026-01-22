import pytest
import requests


@pytest.fixture(scope="session")
def base_url() -> str:
    return "http://localhost:5000"


@pytest.fixture(scope="session")
def api_client(base_url: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def valid_command_payload():
    return {
        "device_id": "sensor-1",
        "command": "RESTART"
    }


@pytest.fixture
def invalid_command_payload():
    return {
        "device_id": "",
        "command": "RESTART"
    }
