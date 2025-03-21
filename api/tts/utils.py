import os
import socket
import time
import uuid


def is_port_in_use(port, host="0.0.0.0"):
    """Check if a port is in use by trying to connect to it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
            return True
        except Exception as e:
            return False


def wait_for_port(port, host="0.0.0.0", timeout=60, interval=1):
    """
    Wait until the given port is in use (i.e. a server is running on it)
    or until the timeout (in seconds) is reached.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port, host):
            return True
        time.sleep(interval)
    return False


def uuid_filename(instance, filename):
    print("instance", instance, filename)
    ext = os.path.splitext(filename)[1]
    return os.path.join('uploads', f"{uuid.uuid4().hex}{ext}")
