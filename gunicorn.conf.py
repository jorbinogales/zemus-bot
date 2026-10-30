import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"
timeout = 300
graceful_timeout = 60
workers = 1
worker_class = "gthread"
threads = 4
keepalive = 5
