# gunicorn.conf.py

# Set the Gunicorn worker timeout to 60 seconds (adjust as needed)
bind = "0.0.0.0:8000"
workers = 4
timeout = 600
loglevel = "info"
