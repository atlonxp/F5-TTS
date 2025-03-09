#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import atexit
import os
import socket
import sys
import threading
import time


def is_port_in_use(port, host="127.0.0.1"):
    """Check if a port is in use by trying to connect to it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
            return True
        except Exception:
            return False


def wait_for_port(port, host="127.0.0.1", timeout=60, interval=1):
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


def start_gradio():
    try:
        from f5_tts.infer import infer_basic_tts
    except ImportError as exc:
        print("Failed to import infer_gradio:", exc)
        return
    # Launch Gradio and capture the server object.
    gradio_server = infer_basic_tts.app.queue(api_open=True).launch(
        server_name="127.0.0.1",
        server_port=55556,
        share=False,
        show_api=True,
        inbrowser=False,
    )
    # Register a shutdown hook to gracefully close Gradio when the process exits.
    atexit.register(gradio_server.close)


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Only when running the development server, launch Gradio concurrently.
    # if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
    #     if is_port_in_use(55556):
    #         print("Gradio server already running on port 55556.")
    #     else:
    #         print("Starting F5-TTS Gradio app concurrently in a separate process...")
    #         gradio_thread = threading.Thread(target=start_gradio, daemon=True)
    #         gradio_thread.start()
    #
    #         print("Waiting for Gradio server to start on port 55556...")
    #         if wait_for_port(55556, "127.0.0.1", timeout=60, interval=1):
    #             print("Gradio server is up!")
    #         else:
    #             print("Warning: Timeout reached. Gradio server did not start in time.")

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
