import pyautogui
import cv2
import numpy as np
import win32gui
import time
from datetime import datetime
import os
import requests
import base64 
from action_model.macro_api import is_number


import os
from datetime import datetime
import cv2


def save_screenshot_with_timestamp(screenshot, save_folder="screenshots", format="png", issue_name=None, folder_timestamp = None):
    """
    Saves a screenshot to a folder with a timestamped filename, handling various image types.

    Args:
        screenshot (np.ndarray, cv2.UMat, or PIL.Image.Image): The screenshot.
        save_folder (str): The folder to save the screenshot to.
        format (str): The desired image format (e.g., "png", "jpg", "jpeg").
        issue_name (str, optional): The name of the issue to include in the folder path.

    Returns:
        str: The absolute path to the saved screenshot, or None if saving fails.
    """
    # Create the base save folder if it doesn't exist
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # Generate a timestamped folder name if issue_name is provided
    if issue_name:
        folder_name = f"{issue_name}_{folder_timestamp}"
        save_folder = os.path.join(save_folder, folder_name)
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

    # Generate a timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"screenshot_{timestamp}.{format}"
    filepath = os.path.join(save_folder, filename)

    # Get the absolute path
    absolute_filepath = os.path.abspath(filepath)

    # Handle different input types
    if isinstance(screenshot, str):
        # If it's a file path, try to read the image
        try:
            img = cv2.imread(screenshot)
            if img is None:
                raise ValueError(f"Could not read image from path: {screenshot}")
        except Exception as e:
            print(f"Error reading image from path: {e}")
            return None
    elif isinstance(screenshot, type(cv2.UMat())):
        # Convert UMat to NumPy array if needed
        img = screenshot.get()
    elif isinstance(screenshot, np.ndarray):
        img = screenshot
    elif hasattr(screenshot, 'tobytes') and hasattr(screenshot, 'size') and hasattr(screenshot, 'mode'): #PIL.Image.Image
         # If it's a PIL Image, convert it to a NumPy array (OpenCV compatible)
        try:
            img = np.array(screenshot)
            # Convert RGB to BGR if necessary
            if screenshot.mode == 'RGB':
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"Error converting PIL Image to NumPy array: {e}")
            return None
    else:
        print("Invalid input type: Screenshot must be a NumPy array, cv2.UMat, PIL Image, or a file path.")
        return None

    # Save the screenshot using OpenCV
    try:
        cv2.imwrite(absolute_filepath, img)
        return absolute_filepath
    except Exception as e:
        print(f"Error saving screenshot: {e}")
        return None

def take_screenshot_of_minecraft_window(window_title_prefix="Minecraft", delay=0.02, save_folder="screenshots", issue_name=None, folder_timestamp = None):
    """
    Takes a screenshot of the Minecraft window and saves it using save_screenshot_with_timestamp.

    Args:
        window_title_prefix (str): The prefix of the Minecraft window title.
        delay (float): Delay in seconds to allow the window to come to the foreground.
        save_folder (str): The folder to save the screenshots to.
        issue_name (str, optional): The name of the issue to include in the folder path.

    Returns:
        str: The path to the saved screenshot, or None if the window is not found or saving fails.
    """

    # Find the Minecraft window by its title prefix
    minecraft_window = None
    for window in pyautogui.getAllWindows():
        if window.title.startswith(window_title_prefix):
            minecraft_window = window
            break

    if minecraft_window is None:
        print(f"Error: Could not find window with title starting with '{window_title_prefix}'")
        return None
    
    # Bring the window to the foreground (optional, but can improve reliability)
    try:
        minecraft_window.activate()
    except Exception as e:
        print(f"Warning: Could not bring window to foreground. {e}")
    time.sleep(delay)

    # Get the window's bounding rectangle
    rect = (minecraft_window.left, minecraft_window.top, minecraft_window.width, minecraft_window.height)

    # Take a screenshot of the specified region
    screenshot = pyautogui.screenshot(region=rect)

    # Convert the PIL Image object to a NumPy array (OpenCV format)
    screenshot_np = np.array(screenshot)
    screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

    # Save the screenshot using the separate function
    return save_screenshot_with_timestamp(screenshot_np, save_folder, issue_name=issue_name, folder_timestamp = folder_timestamp)


def send_commands_to_macro(commands: list[str]):
    """
    Sends a list of commands to the FastAPI endpoint for execution.

    Args:
        commands: A list of strings, where each string is a command 
                  in the format "command_name(arg1, arg2, ...)"
    """
    url = "http://localhost:8500/execute"  # Assuming the API is running locally on port 8500
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=commands, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        print(f"API response: {response.json()}")

    except requests.exceptions.ConnectionError as e:
        print(f"Error: Could not connect to the API. Is the server running? Details: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"API request failed with status code {response.status_code}: {response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def read_in_base64(filepath):
    with open(filepath, 'rb') as image_file:
            image_byte = image_file.read()
            base64_encoded_data = base64.b64encode(image_byte)
            base64_string = base64_encoded_data.decode('utf-8')
    return base64_string

def format_data_as_table(data):
  """
  Formats a list of dictionaries into a table-like string, excluding 'bbox' 
  information and including an index column.

  Args:
    data: A list of dictionaries, where each dictionary represents an item 
          with 'type', 'bbox', 'interactivity', and 'content' keys.

  Returns:
    A string representing the formatted table.
  """

  if not data:
    return "Empty data provided."

  # Extract relevant headers (keys) from the first item, excluding 'bbox'
  headers = ['index'] + [key for key in data[0].keys() if key not in []]

  # Create the table header row
  table_string = "| " + " | ".join(header.title() for header in headers) + " |\n"

  # Create the separator row
  table_string += "|-" + "-|-".join("-" * len(header) for header in headers) + "-|\n"

  # Add data rows with index
  for index, item in enumerate(data):
    row = [str(index)] + [str(item.get(header, "")) for header in headers[1:]]
    table_string += "| " + " | ".join(row) + " |\n"

  return table_string

def format_iterations(iterations):
    """
    Formats an array of iterations into a string representation.

    Args:
        iterations: A list of dictionaries, where each dictionary represents an iteration 
                    and contains keys like "current_title", "thought", "action", and "reflection".
                    The "reflection" key itself contains a dictionary with "text" and "classification".

    Returns:
        A formatted string representing the iterations, or "No previous iterations exist." if the list is empty.
    """

    if not iterations:
        return "No previous iterations exist."

    formatted_string = ""
    for i, iteration in enumerate(iterations):
        formatted_string += f"Iteration {i + 1}\n"
        formatted_string += f"Current Step Title: {iteration.get('current_title', 'N/A')}\n"  # Handle cases where a key might be missing
        formatted_string += f"Thought: {iteration.get('thought', 'N/A')}\n"
        formatted_string += f"Action: {iteration.get('action', 'N/A')}\n"

        reflection = iteration.get('reflection')
        if reflection:
            formatted_string += "Reflection:\n"
            formatted_string += f"  Text: {reflection.get('text', 'N/A')}\n"
            formatted_string += f"  Classification: {reflection.get('classification', 'N/A')}\n"
        else:
            formatted_string += "Reflection: N/A\n"

        formatted_string += "\n"  # Add extra newline for separation between iterations

    return formatted_string

def format_commands(commands: list[str], annotation_list: list[dict] = None) -> str:
    """
    Formats a list of commands into a readable string, using content field from 
    annotation table when available.

    Args:
        commands: A list of strings representing commands.
        annotation_list: A list of dictionaries representing annotations, 
                         where each dictionary has at least a 'content' key.

    Returns:
        A formatted string representing the commands.
    """
    if not commands:
        return "No commands provided."

    formatted_string = ""
    for command in commands:
        parts = command.split("(", 1)
        if len(parts) != 2:
            formatted_string += f"- {command} (Invalid format)\n"
            continue

        command_name = parts[0].strip()
        arguments = parts[1].rstrip(")").split(",")

        if command_name == "click_place" and annotation_list:
            try:
                index = int(arguments[0].strip())
                if 0 <= index < len(annotation_list):
                    content = annotation_list[index].get("content", "N/A")
                    bbox = annotation_list[index].get("bbox", "N/A")
                    formatted_string += f"- Clicked the place that had content: {content} at coordinates: {bbox}\n"
                    print(f"- Clicked the place that had content: {content} at coordinates: {bbox}")
                else:
                    formatted_string += f"- Invalid click_place index: {index}\n"
            except ValueError:
                formatted_string += f"- Invalid click_place argument: {arguments[0]}\n"
        elif command_name == "press":
            if len(arguments) == 1:
                key = arguments[0].strip().strip('"').strip("'")
                formatted_string += f"- Pressed {key} key.\n"
            elif len(arguments) == 2:
                key = arguments[0].strip().strip('"').strip("'")
                duration = arguments[1].strip()
                if is_number(duration):
                    formatted_string += f"- Pressed {key} key for {duration} seconds.\n"
                else:
                    formatted_string += f"- Pressed both {key} key and {duration} key at once.\n"
            else:
                 formatted_string += f"- Invalid press arguments\n"
        elif command_name == "click":
            if len(arguments) == 2:
                x = arguments[0].strip()
                y = arguments[1].strip()
                formatted_string += f"- Clicked at coordinates ({x}, {y}).\n"
            else:
                formatted_string += f"- Invalid click arguments\n"

        elif command_name == "command":
            command_text = arguments[0].strip().strip('"')
            formatted_string += f"- Tried executing command: {command_text}\n"
        elif command_name == "wait":
            duration = arguments[0].strip()
            formatted_string += f"- Waited for {duration} seconds.\n"
        else:
            formatted_string += f"- {command} (Unknown command)\n"

    return formatted_string