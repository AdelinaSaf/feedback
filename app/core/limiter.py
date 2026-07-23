"""
Модуль rate limiting через slowapi.
Лимит: 5 запросов в минуту на IP-адрес.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
