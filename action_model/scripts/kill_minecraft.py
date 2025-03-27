import psutil
import os
import sys

def kill_all_processes_except_cmd_python_uvicorn():
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

if __name__ == "__main__":
    if os.name == 'nt':
        print("WARNING: This script can kill important processes. Proceed with extreme caution.\n")
        kill_all_processes_except_cmd_python_uvicorn()
    else:
        print("This script is designed for Windows operating systems.")