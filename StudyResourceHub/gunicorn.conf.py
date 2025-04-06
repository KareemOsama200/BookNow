# Gunicorn configuration file
# https://docs.gunicorn.org/en/stable/configure.html

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Reuse port
reuse_port = True

# Automatically reload application on code changes
reload = True

# Process naming
proc_name = "educational_platform"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Request settings
limit_request_line = 8190
limit_request_fields = 200
limit_request_field_size = 16380
max_request_line = 0

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'