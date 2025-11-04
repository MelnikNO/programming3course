from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import requests
import time
from datetime import datetime
from typing import List, Dict, Any
from threading import Thread, Event
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


class CurrencySubject:
    """Субъект (Subject) для отслеживания изменений курсов валют"""

    def __init__(self):
        self._observers: List[CurrencyObserver] = []
        self._current_rates: Dict[str, float] = {}
        self._previous_rates: Dict[str, float] = {}
        self._clients: Dict[str, Any] = {}

    def attach(self, observer: 'CurrencyObserver') -> None:
        """Присоединить наблюдателя к субъекту"""
        if observer not in self._observers:
            self._observers.append(observer)
            logger.info(f"Наблюдатель {observer.observer_id} присоединен")

    def detach(self, observer: 'CurrencyObserver') -> None:
        """Отсоединить наблюдателя от субъекта"""
        if observer in self._observers:
            self._observers.remove(observer)
            logger.info(f"Наблюдатель {observer.observer_id} отсоединен")

    def notify(self, currency_data: Dict[str, Any]) -> None:
        """Уведомить всех наблюдателей об изменении курсов"""
        for observer in self._observers:
            observer.update(currency_data)

    def register_client(self, client_id: str, socketio_handler):
        """Зарегистрировать WebSocket клиента"""
        observer = WebSocketObserver(client_id, socketio_handler)
        self.attach(observer)
        self._clients[client_id] = observer
        return observer

    def unregister_client(self, client_id: str):
        """Удалить WebSocket клиента"""
        if client_id in self._clients:
            observer = self._clients[client_id]
            self.detach(observer)
            del self._clients[client_id]

    def get_clients_count(self) -> int:
        """Получить количество подключенных клиентов"""
        return len(self._clients)

    def fetch_currency_rates(self) -> Dict[str, Any]:
        """Получить текущие курсы валют с API Центробанка"""
        try:
            response = requests.get(CBR_API_URL, timeout=10)
            response.raise_for_status()
            data = response.json()

            currencies = {
                'USD': data['Valute']['USD']['Value'],
                'EUR': data['Valute']['EUR']['Value'],
                'GBP': data['Valute']['GBP']['Value'],
                'CNY': data['Valute']['CNY']['Value'],
                'JPY': data['Valute']['JPY']['Value'] / 100,
                'CHF': data['Valute']['CHF']['Value'],
                'CAD': data['Valute']['CAD']['Value']
            }

            changes = self._check_changes(currencies)

            result = {
                'timestamp': datetime.now().isoformat(),
                'rates': currencies,
                'changes': changes,
                'previous_rates': self._previous_rates.copy(),
                'observers_count': self.get_clients_count()
            }

            self._previous_rates = currencies.copy()
            self._current_rates = currencies.copy()

            return result

        except requests.RequestException as e:
            logger.error(f"Ошибка при получении данных: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'rates': self._current_rates,
                'changes': {},
                'error': str(e),
                'observers_count': self.get_clients_count()
            }

    def _check_changes(self, new_rates: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Проверить изменения курсов валют"""
        changes = {}

        for currency, new_rate in new_rates.items():
            if currency in self._previous_rates:
                old_rate = self._previous_rates[currency]
                if abs(old_rate - new_rate) > 0.0001:
                    changes[currency] = {
                        'old_rate': old_rate,
                        'new_rate': new_rate,
                        'change': new_rate - old_rate,
                        'change_percent': ((new_rate - old_rate) / old_rate) * 100
                    }

        return changes


class CurrencyObserver:
    """Абстрактный класс наблюдателя"""

    def __init__(self, observer_id: str):
        self.observer_id = observer_id

    def update(self, currency_data: Dict[str, Any]) -> None:
        """Обновить данные наблюдателя"""
        raise NotImplementedError


class WebSocketObserver(CurrencyObserver):
    """Наблюдатель, который отправляет данные через WebSocket"""

    def __init__(self, observer_id: str, socketio_handler):
        super().__init__(observer_id)
        self.socketio_handler = socketio_handler

    def update(self, currency_data: Dict[str, Any]) -> None:
        """Отправить обновление через WebSocket"""
        message = {
            'type': 'currency_update',
            'observer_id': self.observer_id,
            'data': currency_data,
            'timestamp': datetime.now().isoformat()
        }

        try:
            self.socketio_handler.emit('currency_data', message)
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения наблюдателю {self.observer_id}: {e}")


class CurrencyMonitor:
    """Монитор для периодической проверки курсов валют"""

    def __init__(self, subject: CurrencySubject, interval: int = 30):
        self.subject = subject
        self.interval = interval  # интервал в секундах
        self.thread = None
        self.stop_event = Event()

    def start_monitoring(self):
        """Запустить мониторинг курсов валют в отдельном потоке"""
        if self.thread and self.thread.is_alive():
            logger.info("Мониторинг уже запущен")
            return

        self.stop_event.clear()
        self.thread = Thread(target=self._monitoring_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Мониторинг курсов валют запущен (интервал: {self.interval} сек)")

    def stop_monitoring(self):
        """Остановить мониторинг"""
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join()
            logger.info("Мониторинг курсов валют остановлен")

    def _monitoring_loop(self):
        """Цикл мониторинга"""
        while not self.stop_event.is_set():
            try:
                currency_data = self.subject.fetch_currency_rates()

                if currency_data.get('changes'):
                    logger.info(f"Обнаружены изменения курсов: {list(currency_data['changes'].keys())}")
                    self.subject.notify(currency_data)

                    socketio.emit('currency_update', {
                        'type': 'broadcast_update',
                        'data': currency_data,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    logger.info(f"Проверка курсов завершена. Изменений нет. ({currency_data['timestamp']})")

                self.stop_event.wait(self.interval)

            except Exception as e:
                logger.error(f"Ошибка в мониторинге: {e}")
                self.stop_event.wait(self.interval)

    def set_interval(self, interval: int):
        """Установить новый интервал мониторинга"""
        self.interval = interval
        logger.info(f"Интервал мониторинга изменен на {interval} сек")


# Глобальные экземпляры
currency_subject = CurrencySubject()
currency_monitor = CurrencyMonitor(currency_subject, interval=30)


@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/status')
def status():
    """Статус сервера"""
    return jsonify({
        'status': 'running',
        'observers_count': currency_subject.get_clients_count(),
        'monitoring_interval': currency_monitor.interval,
        'is_monitoring': currency_monitor.thread and currency_monitor.thread.is_alive(),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/rates')
def get_rates():
    """API для получения текущих курсов валют"""
    currency_data = currency_subject.fetch_currency_rates()
    return jsonify(currency_data)


@socketio.on('connect')
def handle_connect():
    """Обработчик подключения WebSocket клиента"""
    client_id = f"observer_{int(time.time() * 1000)}"

    observer = currency_subject.register_client(client_id, socketio)

    logger.info(f"Клиент подключен: {client_id} (SID: {request.sid})")

    emit('connection_established', {
        'observer_id': client_id,
        'message': 'Вы успешно подключились к мониторингу курсов валют',
        'timestamp': datetime.now().isoformat(),
        'clients_count': currency_subject.get_clients_count()
    })

    currency_data = currency_subject.fetch_currency_rates()
    emit('currency_data', {
        'type': 'initial_data',
        'observer_id': client_id,
        'data': currency_data,
        'timestamp': datetime.now().isoformat()
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Обработчик отключения WebSocket клиента"""
    client_id = None
    for cid, observer in currency_subject._clients.items():
        client_id = cid
        break

    if client_id:
        currency_subject.unregister_client(client_id)
        logger.info(f"Клиент отключен: {client_id}")

        socketio.emit('clients_update', {
            'clients_count': currency_subject.get_clients_count(),
            'timestamp': datetime.now().isoformat()
        })


@socketio.on('get_rates')
def handle_get_rates():
    """Обработчик запроса текущих курсов"""
    client_id = None
    for cid, observer in currency_subject._clients.items():
        client_id = cid
        break

    currency_data = currency_subject.fetch_currency_rates()
    emit('currency_data', {
        'type': 'current_rates',
        'observer_id': client_id,
        'data': currency_data,
        'timestamp': datetime.now().isoformat()
    })


@socketio.on('set_interval')
def handle_set_interval(data):
    """Обработчик изменения интервала мониторинга"""
    interval = data.get('interval', 30)
    currency_monitor.set_interval(interval)

    client_id = None
    for cid, observer in currency_subject._clients.items():
        client_id = cid
        break

    emit('interval_updated', {
        'observer_id': client_id,
        'interval': interval,
        'timestamp': datetime.now().isoformat()
    })


@socketio.on('start_monitoring')
def handle_start_monitoring():
    """Обработчик запуска мониторинга"""
    currency_monitor.start_monitoring()
    emit('monitoring_started', {
        'interval': currency_monitor.interval,
        'timestamp': datetime.now().isoformat()
    })


@socketio.on('stop_monitoring')
def handle_stop_monitoring():
    """Обработчик остановки мониторинга"""
    currency_monitor.stop_monitoring()
    emit('monitoring_stopped', {
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    currency_monitor.start_monitoring()
    logger.info("Сервер запускается на http://localhost:5000")
    logger.info("Доступные endpoints:")
    logger.info("  /          - Главная страница с WebSocket подключением")
    logger.info("  /status    - Статус сервера")
    logger.info("  /api/rates - Текущие курсы валют (JSON API)")
    socketio.run(app,
                 host='0.0.0.0',
                 port=5000,
                 debug=True,
                 allow_unsafe_werkzeug=True)