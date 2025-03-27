import minecraft_launcher_lib
import subprocess
import sys
import os
import time
import win32gui
import win32con
import uuid
from queue import Queue, Empty
from threading import Thread
import psutil
import os

def kill_all_processes_except_cmd_python():
    """Kills all processes EXCEPT those named cmd.exe (or Command Prompt), system processes, python processes, and uvicorn processes."""

    killed_count = 0
    try:
        for process in psutil.process_iter(['pid', 'name', 'username', 'exe']):
            try:
                process_name = process.info['name'].lower()
                process_exe = process.info['exe']

                # Skip cmd.exe or Command Prompt
                if process_name == "cmd.exe" or process_name == "command prompt":
                    print(f"Skipping cmd process: {process_name} (PID: {process.info['pid']})")
                    continue

                # Skip likely system processes based on path and name
                if process_exe is not None and "windows" in process_exe.lower() and "system32" in process_exe.lower():
                    print(f"Skipping system process: {process_name} (PID: {process.info['pid']})")
                    continue

                # Skip processes with 'system' in the name
                if "system" in process_name:
                    print(f"Skipping system process: {process_name} (PID: {process.info['pid']})")
                    continue

                # Skip processes run by the SYSTEM user
                if process.info['username'] == 'SYSTEM':
                    print(f"Skipping system process: {process_name} (PID: {process.info['pid']})")
                    continue

                # Skip Python processes (name starts with 'python')
                if process_name.startswith("python"):
                    print(f"Skipping python process (name starts with 'python'): {process_name} (PID: {process.info['pid']})")
                    continue

                # Skip Python processes (exe ends with '.exe' and path contains 'python')
                if process_exe is not None and process_exe.lower().endswith(".exe") and "python" in process_exe.lower():
                    print(f"Skipping python process (exe with 'python' in path): {process_name} (PID: {process.info['pid']})")
                    continue

                # Skip Uvicorn processes
                if process_name == "uvicorn.exe":
                    print(f"Skipping uvicorn process: {process_name} (PID: {process.info['pid']})")
                    continue

                # Kill the process if it doesn't match any of the above conditions
                print(f"Killing process: {process.info['name']} (PID: {process.info['pid']})")
                process.kill()
                killed_count += 1

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                print(f"Skipping process due to exception (possibly ended or permissions issue)")
            except Exception as e:
                print(f"Error during the process execution: {e}")
    except Exception as e:
        print(f"Error during process enumeration: {e}")
    finally:
        print(f"\nFinished, {killed_count} processes were killed.")

class MinecraftLauncher:
    """
    A class to handle the installation, login, and launching of Minecraft,
    and manage the Minecraft process output.
    """

    def __init__(self, version="1.14.3", use_microsoft_login=False, client_id=None, redirect_url=None):
        """
        Initializes the MinecraftLauncher with the specified version and login settings.

        Args:
            version (str): The desired Minecraft version.
            use_microsoft_login (bool): Whether to use Microsoft account login.
            client_id (str): The Azure Application Client ID for Microsoft login.
            redirect_url (str): The Azure Application Redirect URL for Microsoft login.
        """
        self.version = version
        self.use_microsoft_login = use_microsoft_login
        self.client_id = client_id
        self.redirect_url = redirect_url
        self.minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        self.process = None
        self.output_queue = Queue()
        self.error_queue = Queue()
        self.output_thread = None
        self.error_thread = None
        self.log_file_path = os.path.join(self.minecraft_directory, "logs", "latest.log")
        self.log_file = None  # File object for latest.log

    def microsoft_login(self):
        """Handles Microsoft account login flow."""
        if not self.client_id or not self.redirect_url:
            raise ValueError("Client ID and Redirect URL must be set for Microsoft login.")

        login_url, state, code_verifier = minecraft_launcher_lib.microsoft_account.get_secure_login_data(
            self.client_id, self.redirect_url
        )
        print(f"Please open {login_url} in your browser and copy the url you are redirected into the prompt below.")
        code_url = input("Paste the redirect URL here: ")

        try:
            auth_code = minecraft_launcher_lib.microsoft_account.parse_auth_code_url(code_url, state)
        except AssertionError:
            print("States do not match! Make sure you copied the URL correctly.")
            sys.exit(1)
        except KeyError:
            print("URL not valid. Make sure you copied the URL correctly.")
            sys.exit(1)

        login_data = minecraft_launcher_lib.microsoft_account.complete_login(
            self.client_id, None, self.redirect_url, auth_code, code_verifier
        )
        return login_data
    def kill_minecraft(self):
        """Kills the Minecraft process."""
        if self.process:
            print(f"Killing Minecraft process (PID: {self.process.pid})...")
            self.process.kill()
            self.process = None
            print("Minecraft process killed.")
        else:
            print("Minecraft process is not running.")
        kill_all_processes_except_cmd_python()
    
    def set_always_on_top(self, hwnd):
        """Sets the window with the given handle to be always on top."""
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

    def install_minecraft(self):
        """Installs the specified Minecraft version."""
        try:
            print(f"Installing Minecraft version {self.version}...")
            minecraft_launcher_lib.install.install_minecraft_version(self.version, self.minecraft_directory)
            print(f"Minecraft {self.version} installed successfully!")
        except Exception as e:
            print(f"Error installing Minecraft: {e}")
            sys.exit(1)

    def launch_minecraft(self):
        """Launches Minecraft and starts threads to capture output."""
        # Delete the log file if it exists
        if os.path.exists(self.log_file_path):
            try:
                os.remove(self.log_file_path)
                print(f"Deleted existing log file: {self.log_file_path}")
            except Exception as e:
                print(f"Error deleting log file: {e}")
                # You might want to handle this more gracefully, e.g., warn the user but continue

        # Login (if enabled)
        if self.use_microsoft_login:
            try:
                login_data = self.microsoft_login()
                print(f"Logged in as {login_data['name']}!")
                options = {
                    "username": login_data["name"],
                    "uuid": login_data["id"],
                    "token": login_data["access_token"]
                }
            except Exception as e:
                print(f"Error during Microsoft login: {e}")
                sys.exit(1)
        else:
            # Offline mode (generate a random UUID)
            offline_uuid = str(uuid.uuid4())
            options = {
                "username": "Player",
                "uuid": offline_uuid,
                "token": ""
            }

        # Launch Minecraft
        try:
            print(f"Launching Minecraft {self.version}...")
            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
                self.version, self.minecraft_directory, options
            )

            # Start Minecraft in a new subprocess
            self.process = subprocess.Popen(
                minecraft_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.minecraft_directory,  # Set working directory for relative paths
                creationflags=subprocess.CREATE_NEW_CONSOLE # Added to make the subprocess run in a new console
            )
            print(f"Minecraft launched! (PID: {self.process.pid})")

            # Start threads to capture output and error streams
            self.output_thread = Thread(target=self._enqueue_output, args=(self.process.stdout, self.output_queue))
            self.error_thread = Thread(target=self._enqueue_output, args=(self.process.stderr, self.error_queue))
            self.output_thread.daemon = True
            self.error_thread.daemon = True
            self.output_thread.start()
            #self.error_thread.start()

            # Start the log file monitoring thread
            """self.log_monitor_thread = Thread(target=self._monitor_log_file)
            self.log_monitor_thread.daemon = True
            self.log_monitor_thread.start()"""

        except Exception as e:
            print(f"Error launching Minecraft: {e}")
            sys.exit(1)

    def _monitor_log_file(self):
        """Monitors the latest.log file periodically."""
        while self.is_minecraft_running():
            try:
                if not self.log_file:
                    if os.path.exists(self.log_file_path):
                        self.log_file = open(self.log_file_path, "r")
                        print(f"Started monitoring log file: {self.log_file_path}")
                else:
                    line = self.log_file.readline()
                    if line:
                        self.output_queue.put(line)

            except Exception as e:
                print(f"Error reading log file: {e}")
                self.log_file = None  # Reset log_file on error to retry opening it

            time.sleep(0.2)  # Check for the log file every 0.2 seconds

        # Close the log file if it was opened
        if self.log_file:
            self.log_file.close()
            self.log_file = None

    def _enqueue_output(self, out_stream, queue):
        """
        Helper function to continuously read from a stream and put lines into a queue.

        Args:
            out_stream: The output stream (stdout or stderr).
            queue: The queue to put lines into.
        """
        for line in iter(out_stream.readline, b''):
            queue.put(line.decode("utf-8"))
        out_stream.close()

    def get_minecraft_output(self, timeout=None):
        """
        Retrieves the next line from the Minecraft output queue.

        Args:
            timeout (float, optional): Maximum time to wait for a line.

        Returns:
            str: The next line from the output, or None if timeout occurs.
        """
        try:
            return self.output_queue.get(timeout=timeout)
        except Empty:
            return None

    def get_minecraft_errors(self, timeout=None):
        """
        Retrieves the next line from the Minecraft error queue.

        Args:
            timeout (float, optional): Maximum time to wait for a line.

        Returns:
            str: The next line from the error stream, or None if timeout occurs.
        """
        try:
            return self.error_queue.get(timeout=timeout)
        except Empty:
            return None

    def is_minecraft_running(self):
        """
        Checks if the Minecraft process is still running.

        Returns:
            bool: True if Minecraft is running, False otherwise.
        """
        return self.process is not None and self.process.poll() is None

    def wait_for_minecraft(self):
        """Waits for the Minecraft process to terminate."""
        if self.process:
            self.process.wait()

    def terminate_minecraft(self):
        """Terminates the Minecraft process."""
        if self.process:
            self.process.terminate()

    def __del__(self):
        """
        Ensures that the Minecraft process is terminated when the object is deleted.
        """
        self.terminate_minecraft()

def launch_minecraft(version):
    launcher = MinecraftLauncher(
        version=version,
        use_microsoft_login=False,  # Set to True to use Microsoft login
        # client_id="YOUR_CLIENT_ID",  # Replace with your Client ID if using Microsoft login
        # redirect_url="YOUR_REDIRECT_URL"  # Replace with your Redirect URL if using Microsoft login
    )
    launcher.install_minecraft()
    launcher.launch_minecraft()
    return launcher

if __name__ == "__main__":
    print(minecraft_launcher_lib.utils.get_minecraft_directory())
    # Example usage:
    launcher = MinecraftLauncher(
        version="1.14.3",
        use_microsoft_login=False,  # Set to True to use Microsoft login
        # client_id="YOUR_CLIENT_ID",  # Replace with your Client ID if using Microsoft login
        # redirect_url="YOUR_REDIRECT_URL"  # Replace with your Redirect URL if using Microsoft login
    )

    launcher.install_minecraft()
    launcher.launch_minecraft()

    # Continuously monitor Minecraft output
    while launcher.is_minecraft_running():
        output_line = launcher.get_minecraft_output(timeout=0.1)
        if output_line:
            print(f"Minecraft output: {output_line.strip()}")

        error_line = launcher.get_minecraft_errors(timeout=0.1)
        if error_line:
            print(f"Minecraft error: {error_line.strip()}")

        time.sleep(0.1)

    print("Minecraft has exited.")