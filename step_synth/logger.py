import threading
import json
import time
from datetime import datetime

class Logger:
    def __init__(self, log_to_file=False):
        self.messages = []
        self.condition = threading.Condition()
        self.log_to_file = log_to_file
        self.log_file = None

        if self.log_to_file:
            # Create a log file with a timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = open(f"step_log_{timestamp}.txt", "a", encoding="utf-8")

    def log(self, message, message_type="log"):
        with self.condition:
            self.messages.append((message_type, message))
            self.condition.notify_all()

            if self.log_to_file and self.log_file:
                # Write the log message to the file
                log_entry = f"{datetime.now()} [{message_type}] {message}\n"
                self.log_file.write(log_entry)
                self.log_file.flush()  # Ensure the message is written to disk immediately

    def stream_messages(self):
        index = 0
        while True:
            with self.condition:
                while index >= len(self.messages):
                    self.condition.wait()
                if index >= len(self.messages):
                    break  # Exit loop if no more messages
                message_type, message = self.messages[index]
                index += 1
                if message_type == "end" and not self.log_to_file:
                    yield json.dumps({"type": message_type, "message": message})
                    break  # Stop iteration when "end" is encountered
                yield json.dumps({"type": message_type, "message": message})

    def close(self):
        if self.log_file:
            self.log_file.close()

# Example usage
logger = Logger(log_to_file=True)