import os

from config import config as app_config

# log everything to console
accesslog = "-"
errorlog = "-"

# other gunicorn configs
bind = f"0.0.0.0:{app_config.PORT}"
workers = os.cpu_count()
threads = os.cpu_count() * 4
worker_class = "worker.Worker"
