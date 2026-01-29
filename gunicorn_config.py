import multiprocessing

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 60  # Increased from default 30s to handle IMAP operations
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "rejection_bucket"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Restart workers after this many requests to prevent memory leaks
max_requests = 1000
max_requests_jitter = 100