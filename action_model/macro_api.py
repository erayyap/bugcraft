from fastapi import FastAPI, HTTPException
import pyautogui
import time
import asyncio
from pydantic import BaseModel
import uvicorn
import threading
import os
import keyboard
import re

def is_number(string):
    """Checks if a string is a number (integer or decimal)."""
    pattern = r"^-?\d+(\.\d+)?$"
    match = re.match(pattern, string)
    return bool(match)

macro_app = FastAPI()

# Global variable to store the last executed command
last_command = None

def mirror_strip(text, chars):
    """
    Removes characters from the beginning and end of a string only if they
    are mirrored (present at the same indices from both ends).

    Args:
        text: The string to strip.
        chars: The characters to potentially remove.

    Returns:
        The stripped string.
    """
    start = 0
    end = len(text) - 1

    while start <= end:
        if text[start] in chars and text[end] in chars and text[start] == text[end]:
            start += 1
            end -= 1
        else:
            break

    return text[start:end+1]

async def execute_command(command_str: str):
    """Parses and executes a single command."""
    global last_command
    parts = command_str.split("(", 1)
    if command_str.startswith("/"):
        command = mirror_strip(mirror_strip(command_str.rstrip(")").strip(), "'"), '"')
        send_minecraft_command(command)
        return
    elif len(parts) != 2:
        raise HTTPException(status_code=400, detail=f"Invalid command format: {command_str}")

    command_name = parts[0].strip()
    try:
        if command_name == "command":
            command = mirror_strip(mirror_strip(parts[1].rstrip(")").strip("\\").strip(), "'"), '"')
            send_minecraft_command(command)
        elif command_name == "write":
            command = mirror_strip(mirror_strip(parts[1].rstrip(")").strip("\\").strip(), "'"), '"')
            keyboard.write(command, delay = 0.01)
        elif command_name == "click":
            x, y = map(float, parts[1].rstrip(")").split(","))
            click_at_relative_pixel(x, y)
        elif command_name == "moveto":
            x, y = map(float, parts[1].rstrip(")").split(","))
            move_to_relative_pixel(x, y)
        elif command_name == "press":
            parts = parts[1].rstrip(")").split(",")
            keys = [part.strip().strip('"').strip("'").lower() for part in parts]
            duration = None

            # Check if the last argument is a number (duration)
            if len(keys) > 1 and is_number(keys[-1]):
                duration = float(keys.pop())

            if len(keys) == 1:
                # Single key or mouse button press
                key = keys[0]
                button = None
                if "right_" in key:
                    button = 'right'
                elif key == "click" or "left_" in key:
                    button = 'left'
                elif "middle_" in key:
                    button = 'middle'

                if button is not None:
                    if duration is not None:
                        # Hold the mouse button for the specified duration
                        pyautogui.mouseDown(button=button)
                        await asyncio.sleep(duration)
                        pyautogui.mouseUp(button=button)
                    else:
                        # Perform a regular click
                        pyautogui.click(button=button)
                else:
                    # Handle keyboard key with or without duration
                    if duration is not None:
                        if key == "backspace":
                            while duration > 0:
                                keyboard.press('backspace')
                                await asyncio.sleep(0.1)
                                duration -= 0.1
                        else:
                            keyboard.press(key)
                            await asyncio.sleep(duration)
                            keyboard.release(key)
                    else:
                        keyboard.send(key)
            elif len(keys) > 1:
                # Multiple key press (hotkey)
                if duration is not None:
                    # Timed hotkey press
                    for key in keys:
                        keyboard.press(key)
                    await asyncio.sleep(duration)
                    for key in reversed(keys):  # Release in reverse order
                        keyboard.release(key)
                else:
                    # Untimed hotkey press
                    keyboard.send("+".join(keys))
            else:
                raise HTTPException(status_code=400, detail="No keys specified for 'press' command.")

            await asyncio.sleep(0.1)
        elif command_name == "wait":
            duration = float(parts[1].rstrip(")"))
            await asyncio.sleep(duration)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown command: {command_name}")

        last_command = command_str  # Update the last command
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid command arguments: {command_str}")

def get_minecraft_window():
    """Gets the first Minecraft window whose title starts with 'Minecraft'."""
    all_windows = pyautogui.getAllWindows()
    for window in all_windows:
        if window.title.startswith("Minecraft"):
            return window
    raise HTTPException(status_code=404, detail="Minecraft window not found.")

def click_at_relative_pixel(relative_x, relative_y, button = "left"):
    """Clicks at the specified (x, y) pixel coordinates relative to the Minecraft window."""
    window = get_minecraft_window()
    window_left = window.left
    window_top = window.top
    window_width = window.width
    window_height = window.height

    # Calculate absolute coordinates
    absolute_x = window_left + (relative_x * window_width)
    absolute_y = window_top + (relative_y * window_height)

    #pyautogui.click(absolute_x, absolute_y)
    pyautogui.moveTo(absolute_x, absolute_y)
    pyautogui.mouseDown(button = button)
    time.sleep(0.02)
    pyautogui.mouseUp(button = button)

def move_to_relative_pixel(relative_x, relative_y):
    """Move mouse to the specified (x, y) pixel coordinates relative to the Minecraft window."""
    window = get_minecraft_window()
    window_left = window.left
    window_top = window.top
    window_width = window.width
    window_height = window.height

    # Calculate absolute coordinates
    absolute_x = window_left + (relative_x * window_width)
    absolute_y = window_top + (relative_y * window_height)

    #pyautogui.click(absolute_x, absolute_y)
    pyautogui.moveTo(absolute_x, absolute_y)

def send_minecraft_command(command):
    """Opens Minecraft chat, types a command, and sends it."""
    global last_command
    window = get_minecraft_window()
    window.activate()

    time.sleep(0.02)  # Give the window time to activate

    # Check if the last command was 'press(t)'
    if not (last_command and last_command.startswith("press(\"t\"")):
        keyboard.send("t")
        time.sleep(0.1)

    keyboard.write(command, delay = 0.01)  # write the command
    time.sleep(0.1)

    # The next command is not relevant anymore, so we always press enter
    keyboard.send("enter")  # Send the command

@macro_app.post("/execute")
async def execute_commands(commands: list[str]):
    """
    Executes a list of commands in sequence.
    """
    for command_str in commands:
        try:
            await execute_command(command_str)
        except HTTPException as e:
            return e  # Return the error immediately if a command fails
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    return {"message": "Commands executed successfully"}

# Global variable to control the server
server_running = True

def check_for_shutdown_command():
    """
    Checks if F12 is pressed and stops the server if it is.
    """
    global server_running
    while server_running:
        if keyboard.is_pressed('f12'):
            print("Shutdown command received (F12).")
            server_running = False
            os._exit(0)  # Forcefully exit the process
        time.sleep(1)  # Check every 1 second

@macro_app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    """
    print("Minecraft Macro API is starting up...")
    try:
        window = get_minecraft_window()
        print(f"Minecraft window found: {window}")
        window.activate()  # Bring the window to the front
    except HTTPException:
        print("Minecraft window not found during startup. Please ensure Minecraft is running.")
    print("Minecraft Macro API started successfully.")

    # Start the shutdown command listener in a separate thread
    shutdown_thread = threading.Thread(target=check_for_shutdown_command)
    shutdown_thread.daemon = True
    shutdown_thread.start()

@macro_app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler.
    """
    print("Minecraft Macro API is shutting down...")

def run_api():
    """
    Runs the FastAPI application using uvicorn.
    """
    global server_running

    # Start the uvicorn server
    uvicorn.run(macro_app, host="0.0.0.0", port=8500)

    server_running = False
    print("Minecraft Macro API has been shut down.")

if __name__ == "__main__":
    run_api()