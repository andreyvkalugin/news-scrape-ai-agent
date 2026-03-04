import functools
import sqlite3
from sqlite3 import Connection

def closable(db=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            conn = sqlite3.connect(db)
            try:
                result = func(self, conn.cursor(), *args, **kwargs)
                conn.commit()
                return result
            finally:
                conn.close() 
        return wrapper
    return decorator