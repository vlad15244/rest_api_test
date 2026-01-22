import pytest
import requests
import time
import logging
from json_valid import validate_response, validate_error

# Конфигурация логирования. Пишем просто в файл test.log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("test.log", mode='w', encoding='utf-8')
    ],
    force=True
)

logger = logging.getLogger(__name__)


def polling_state(
    api_client,
    base_url,
    command_id,
    expected_statuses,
    timeout=10,
    poll_interval=1
):
    logger.info(f"Старт опроса сервера для {command_id}")
    start_time = time.time()
    attempts = 0

    while time.time() - start_time < timeout:
        attempts += 1
        try:
            response = api_client.get(f"{base_url}/api/commands/{command_id}")
            logger.info(f"Попытка запроса {attempts}")
            if response.status_code == 200:
                data = response.json()

                validate_response(data, "test_positive_case/response_200")
                status = data["status"]

                if "status" not in data:
                    logger.warning(
                        f"В ответе отсутствует поле 'status': {data} для попытки {attempts}")
                    return None

                if status in expected_statuses:
                    logger.info(
                        f"Получен ответ от сервера для попытки {attempts}")
                    return data
                else:
                    return None
            else:
                logger.info(f"Попытка {attempts}: HTTP {response.status_code}")

        except requests.RequestException as e:
            logger.info(f"Попытка {attempts}: ошибка запроса: {e}")
            time.sleep(poll_interval)

    final_response = api_client.get(f"{base_url}/api/commands/{command_id}")
    final_data = final_response.json() if final_response.status_code == 200 else {}

    raise TimeoutError(
        f"Таймаут {timeout}с: статус не достиг {expected_statuses} за {attempts} попыток.\n"
        f"Последний статус: {final_data.get('status', 'N/A')}\n"
        f"Последний ответ: {final_data}"
    )


def test_positive_case(api_client, base_url, valid_command_payload):
    logger.info("Запуск теста - Позитивный сценарий")
    """
    Позитивный сценарий:
        1. Создать команду
        2. Дождаться переход в статус 
        3. Проверить результат
    """
    # 1 - Создаем команду
    message_api = api_client.post(
        f"{base_url}/api/commands", json=valid_command_payload)

    assert message_api.status_code == 201, (
        f"Ожидался 201 Created, получен {message_api.status_code}"
    )

    data = message_api.json()
    validate_response(data, "test_positive_case/response_200")
    assert "id" in data, "Ответ не содержит 'id'"
    assert isinstance(data["id"], str), "Значение 'id' не является строкой"
    assert "status" in data, "Поле 'status' отсутствует"
    assert data["status"] == "NEW", f"Ожидаемый статус 'NEW', получен '{data['status']}'"

    command_id = data["id"]

    # 2 - Ожидаем статус
    final_data = polling_state(
        api_client,
        base_url,
        command_id,
        expected_statuses=["SUCCESS", "FAILED"],
        timeout=30
    )

    # 3 - Проверяем результат, смотрим что пришло и уточняем ответ
    assert final_data != None, "Пришел пустой ответ"
    if final_data["status"] == "SUCCESS":
        assert final_data.get(
            "error") == "", "При SUCCESS поле 'error' должно быть пустым"
    else:
        assert final_data["status"] == "FAILED"
        assert "error" in final_data, "При FAILED должно быть поле 'error'"
        assert final_data["error"] == "Device unreachable", (
            f"Ожидаемая ошибка 'Device unreachable', получена '{final_data['error']}'"
        )
    logger.info("Тест пройден успешно")


def test_negative_case(api_client, base_url, invalid_command_payload):
    logger.info("Запуск теста - Негативный сценарий")
    """
    Негативный сценарий :
        1. Отправляем пустой device_id
        2. Смотрим пришел статус 400 - Проверим так же что пришло в ошибке - device_id is empty or missing

    """
    response = api_client.post(
        f"{base_url}/api/commands", json=invalid_command_payload)

    assert response.status_code == 400, (
        f"Ожидался 400 Bad Request, получен {response.status_code}"
    )

    data = response.json()
    validate_error(data, "test_negative_case/response_200")
    assert "error" in data, "Ответ должен содержать поле 'error'"
    assert isinstance(data["error"], str), "Поле 'error' должно быть строкой"
    assert data["error"] == "device_id is empty or missing", (
        f"Ожидаемое сообщение: 'device_id is empty or missing', получено: '{data['error']}'"
    )

    logger.info("Тест пройден успешно")


@pytest.mark.parametrize("command", ["RESTART", "RESET"])
def test_parametrized_commands(api_client, base_url, valid_command_payload, command):
    """
    Параметризованный тест: отправка команд с разными значениями 'command'.
    Проверяет, что API принимает допустимые команды.
    """
    payload = valid_command_payload.copy()
    payload["command"] = command
    logger.info(f"Запуск параметризированного теста - аргумент {command}")

    response = api_client.post(f"{base_url}/api/commands", json=payload)
    assert response.status_code == 201, (
        f"Ошибка для command={command}: статус {response.status_code}"
    )

    data = response.json()
    validate_response(
        data, f"test_parametrized_commands - {command}/response_200")
    assert "id" in data, "Ответ не содержит 'id'"
    assert data["status"] == "NEW", f"Ожидаемый статус 'NEW', получен '{data['status']}'"
    logger.info(f"Параметризирвоанный тест {command} пройден успешно")