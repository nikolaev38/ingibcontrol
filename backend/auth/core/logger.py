import logging, socket, requests, json, time
from loki_logger_handler.loki_logger_handler import LokiLoggerHandler
from core.config import settings


custom_included_fields = ['object_id', 'ip']

class CustomJsonFormatter(logging.Formatter):
    def format(self, record):
        # Получаем стандартные поля
        log_record = {
            "timestamp": int(time.time() * 1000),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "logger": record.name,
            "thread": record.thread,
            "function": record.funcName,
            "file": record.filename,
            "line": record.lineno
        }
        
        # Добавляем исключение, если есть
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        
        # Добавляем пользовательские теги
        if hasattr(record, 'tags') and isinstance(record.tags, dict):
            log_record.update(record.tags)
            
        return json.dumps(log_record, ensure_ascii=False)

class CustomLokiHandler(LokiLoggerHandler):
    def __init__(self, service=None, application=None, environment=None, included_fields=None, **kwargs):
        self.url = settings.loki.url
        # Создаем labels из переданных параметров
        self.labels = {
            'service': service or 'unknown',
            'application': application or 'unknown',
            'environment': environment or 'development',
            'host': socket.gethostname(),
        }
        # Поля, которые будут включены в лог (по умолчанию пустой список - ничего не включать)
        self.included_fields = set(included_fields or [])
        super().__init__(self.url, labels=self.labels, **kwargs)

    def emit(self, record):

        # Получаем теги из record
        tags = getattr(record, 'tags', {})
        if not isinstance(tags, dict):
            tags = {}

        # Создаем основное сообщение с полями
        log_entry = {
            "message": record.getMessage(),
            "level": record.levelname.lower(),
            "timestamp": int(time.time() * 1000),
            "logger": record.name,
            "source": {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName
            }
        }

        # Добавляем пользовательские теги как поля верхнего уровня
        # for key, value in tags.items():
        #     if isinstance(value, (str, int, float, bool, type(None))):
        #         log_entry[key] = value

        # Добавляем только разрешенные поля из тегов
        for field in self.included_fields:
            if field in tags:
                log_entry[field] = tags[field]

        # Формируем финальное сообщение для Loki
        msg = {
            "streams": [{
                "stream": {
                    "application": self.labels['application'],
                    "environment": self.labels['environment'],
                    "service": self.labels['service'],
                    "host": self.labels['host'],
                    "level": record.levelname.lower()
                },
                "values": [
                    [str(int(time.time() * 1e9)), json.dumps(log_entry, ensure_ascii=False)]
                ]
            }]
        }
        # Отправляем сообщение
        self._send_to_loki(msg)

    def _send_to_loki(self, msg):
        """Отправляет сообщение в Loki"""
        headers = {
            'Content-Type': 'application/json',
            'X-Scope-OrgID': 'tenant1'
        }
        
        requests.post(
            self.url,
            data=json.dumps(msg),
            headers=headers,
            timeout=5
        )


logger_config = {
	'version': 1,
	'disable_existing_loggers': False,
	'formatters': {
		'app_format': {
            'format': '{levelname}:{filename}:{lineno} -> {message}',
            'style': '{'
        },
	},
	'handlers': {
		'console': {
			'class': 'logging.StreamHandler',
			'level': 'DEBUG',
			'formatter': 'app_format'
		},
        'site_auth': {
			'()': 'core.logger.CustomLokiHandler',
            'level': 'DEBUG',
            'formatter': 'app_format',
            'service': 'site_auth',
            'application': 'fastapi-auth',
            'environment': 'development',
            'included_fields': custom_included_fields
		},
        'site_endpoints': {
			'()': 'core.logger.CustomLokiHandler',
            'level': 'DEBUG',
            'formatter': 'app_format',
            'service': 'site_endpoints',
            'application': 'fastapi-auth',
            'environment': 'development',
            'included_fields': custom_included_fields
		},
        'model_profile': {
			'()': 'core.logger.CustomLokiHandler',
            'level': 'DEBUG',
            'formatter': 'app_format',
            'service': 'model_profile',
            'application': 'fastapi-auth',
            'environment': 'development',
            'included_fields': custom_included_fields
		},
	},
    'loggers': {
        'site_auth_repository_logger': {
			'level': 'DEBUG',
			'handlers': ['site_auth'],
			'propagate': False
		},
        'site_endpoints_logger': {
			'level': 'DEBUG',
			'handlers': ['site_endpoints'],
			'propagate': False
		},
        'model_profile_logger': {
			'level': 'DEBUG',
			'handlers': ['model_profile'],
			'propagate': False
		},
	},
}