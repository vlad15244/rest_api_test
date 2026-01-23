from flask import Flask, request, jsonify
from datetime import datetime
import threading
import time
import random

app = Flask(__name__)

commands = {}

COMMAND_STATUS = [
    'SUCCESS',
    'FAILED'
]


def execute_command(command_id):
    """
        функция, где имитируем изменение статуса        
    """
    time.sleep(2)

    if command_id in commands:
        # Просто случайный результат для получения статуса

        state = random.choice([0, 1])
        commands[command_id]['status'] = COMMAND_STATUS[state]
        commands[command_id]['error'] = ''

        if COMMAND_STATUS[state] == COMMAND_STATUS[1]:
            commands[command_id]['error'] = 'Device unreachable'


@app.route('/api/commands', methods=['POST'])
def create_command():
    """
    Создание команды.
    """
    data = request.get_json()

    """
    проверка, что device_id пустой - в этом случае формируем код 400 и сообщение
    """
    if 'device_id' not in data or not data['device_id']:
        return jsonify({'error': 'device_id is empty or missing'}), 400

    """
    проверка, что command пустой - в этом случае формируем код 400 и сообщение
    """
    if 'command' not in data or not data['command']:
        return jsonify({'error': 'command is empty or missing'}), 400

    """ 
    Создаём команду - генерируем идентификатор
    ПРОСТО ЦЕЛОЕ ЧИСЛО

    """

    uniq_id = 0
    command_id = str(uniq_id + 1)

    command = {
        'id': command_id,
        'device_id': data['device_id'],
        'command': data['command'],
        'status': 'NEW',
        'error': None
    }
    commands[command_id] = command

    # в новой задаче запускаем выполнение функции, меняющей статусы
    threading.Thread(target=execute_command, args=(command_id,)).start()

    # делаем Респонс с кодом 201
    return jsonify({
        'id': command_id,
        'status': 'NEW'
    }), 201


@app.route('/api/commands/<command_id>', methods=['GET'])
def get_command(command_id):
    """
    Получение статуса
    Проверим корректна ли команда - если нет сформируем ошибку и статус 404
    Если команда корректна сформируем статус 200
    """
    command = commands.get(command_id)
    if not command:
        return jsonify({'error': 'Command not found'}), 404

    return jsonify(command), 200


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
