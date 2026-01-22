from jsonschema import validate, ValidationError

SCHEMA_COMMAND_RESPONSE = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "status": {"type": "string", "enum": ["NEW", "IN_PROGRESS", "SUCCESS", "FAILED"]},
        "command": {"type": "string"},
        'status': {"type": "string"},
        "device_id": {"type": "string"},
        "error": {"type": "string"},
    },
    "required": ["id", "status"],
    "additionalProperties": False
}

SCHEMA_ERROR_RESPONSE = {
    "type": "object",
    "properties": {
        "error": {"type": "string"}
    },
    "required": ["error"],
    "additionalOperations": False
}


def validate_response(data: dict, context: str):
    try:
        validate(instance=data, schema=SCHEMA_COMMAND_RESPONSE)
    except ValidationError as e:
        raise AssertionError(
            f"Неккоректная структура JSON ответа ({context}): {e.message}") from e


def validate_error(data: dict, context: str):
    try:
        validate(instance=data, schema=SCHEMA_ERROR_RESPONSE)
    except ValidationError as e:
        raise AssertionError(
            f"Неккоректная структура JSON ответа ({context}): {e.message}") from e
