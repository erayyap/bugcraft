# Main API
import threading
from action_model.minecraft_runner import launch_minecraft
from action_model.macro_api import run_api as macro_run
import win32gui
import time
from action_model.OmniParser.omniparser import OmniParser
import torch
from action_model.utils import (take_screenshot_of_minecraft_window, 
                   save_screenshot_with_timestamp, 
                   send_commands_to_macro, 
                   read_in_base64, 
                   format_data_as_table, 
                   format_iterations,
                   format_commands)
from action_model.chains import thought_chain, action_chain, reflection_chain, cluster_verification_chain, thought_action_chain, action_correction_chain, self_correction_chain
import pyautogui
from action_model.environment import MAKE_FULLSCREEN, SEPERATE_THOUGHT, USE_CORRECTION
from datetime import datetime
import os
import shutil
import psutil
import glob
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tempfile
import sys

def setup_logging(issue_name):
    """
    Sets up a log file with the current timestamp and issue name.
    Creates a 'logs' directory if it doesn't exist.
    Returns the path to the log file.
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"action_log_{issue_name}_{timestamp}.log"
    log_filepath = os.path.join(log_dir, log_filename)
    return log_filepath

def log_message(message, log_filepath):
    """
    Prints a message to the console and writes it to the log file.
    """
    print(message)
    with open(log_filepath, "a") as log_file:
        log_file.write(message + "\n")
      
class McWorldFolderHandler(FileSystemEventHandler):
    def __init__(self, datapacks, log_filepath):
        self.datapacks = datapacks
        self.log_filepath = log_filepath
        self.mcworld_folder = None
        self.datapack_loaded = False
        
    def on_created(self, event):
        if event.is_directory and "mcworld" in event.src_path.lower():
            self.mcworld_folder = event.src_path
            log_message(f"Detected mcworld folder: {self.mcworld_folder}", self.log_filepath)
            
            # Kill folder explorer windows
            """for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() in ['explorer.exe']:
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass"""

            # Copy datapacks if available
            if self.datapacks:
                datapack_dir = self.mcworld_folder #os.path.join(self.mcworld_folder, "./")
                os.makedirs(datapack_dir, exist_ok=True)
                
                for datapack in self.datapacks:
                    try:
                        datapack_name = os.path.basename(datapack)
                        target_path = os.path.join(datapack_dir, datapack_name)
                        if os.path.isdir(datapack):
                            shutil.copytree(datapack, target_path)
                        else:
                            shutil.copy2(datapack, target_path)
                        log_message(f"Copied datapack from {datapack} to {target_path}", self.log_filepath)
                        self.datapack_loaded = True
                    except Exception as e:
                        log_message(f"Error copying datapack {datapack}: {e}", self.log_filepath)

def load_minecraft_world(world_path, minecraft_saves, issue_name, log_filepath):
    """Handle loading a Minecraft world and saving a copy to issue-specific directory."""
    world_name = os.path.basename(world_path)
    backup_path = os.path.join(minecraft_saves, f"{world_name}_backup")
    
    # Save a copy to issue-specific worlds directory
    issue_worlds_dir = os.path.join("worlds", issue_name)
    os.makedirs(issue_worlds_dir, exist_ok=True)
    issue_world_path = os.path.join(issue_worlds_dir, world_name)
    shutil.copytree(world_path, issue_world_path, dirs_exist_ok=True)
    log_message(f"Saved world copy to {issue_world_path}", log_filepath)
    
    # Backup existing world if any
    if os.path.exists(os.path.join(minecraft_saves, world_name)):
        shutil.move(os.path.join(minecraft_saves, world_name), backup_path)
        log_message(f"Backed up existing world to {backup_path}", log_filepath)

    # Copy new world
    target_path = os.path.join(minecraft_saves, world_name)
    shutil.copytree(world_path, target_path)
    log_message(f"Copied world to {target_path}", log_filepath)
    
    return target_path

def get_minecraft_saves_dir():
    """Get the Minecraft saves directory in a cross-platform way."""
    if os.name == 'nt':  # Windows
        return os.path.join(os.getenv('APPDATA'), '.minecraft', 'saves')
    elif os.name == 'posix':  # Linux/Mac
        if sys.platform == 'darwin':  # Mac
            return os.path.expanduser('~/Library/Application Support/minecraft/saves')
        else:  # Linux
            return os.path.expanduser('~/.minecraft/saves')
    else:
        raise Exception("Unsupported operating system")

def ready_apis(bug_steps, bug_version, issue_name, worlds=None, datapacks=None):
    """
    Main function to handle bug reproduction steps.
    
    Args:
        bug_steps: List of steps to reproduce the bug
        bug_version: Minecraft version to use
        issue_name: Name/ID of the issue being processed
        worlds: List of world directories to be loaded
        datapacks: List of datapack paths to be loaded
    """
    log_filepath = setup_logging(issue_name)
    observer = None
    beginning_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    try:
        log_message(f"Log file created at: {log_filepath}", log_filepath)
        log_message(f"Processing issue: {issue_name}", log_filepath)

        # Clear and prepare minecraft saves folder
        minecraft_saves = get_minecraft_saves_dir()
        if os.path.exists(minecraft_saves):
            for item in os.listdir(minecraft_saves):
                item_path = os.path.join(minecraft_saves, item)
                try:
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    log_message(f"Error clearing saves folder: {e}", log_filepath)

        # Load worlds if provided
        loaded_worlds = []
        if worlds:
            for world in worlds:
                try:
                    target_path = load_minecraft_world(world, minecraft_saves, issue_name, log_filepath)
                    loaded_worlds.append(target_path)
                except Exception as e:
                    log_message(f"Error loading world {world}: {e}", log_filepath)

        # Set up temp folder monitoring if datapacks are provided
        if datapacks:
            temp_dir = tempfile.gettempdir()
            event_handler = McWorldFolderHandler(datapacks, log_filepath)
            observer = Observer()
            observer.schedule(event_handler, temp_dir, recursive=False)
            observer.start()
            log_message("Started monitoring temp directory for mcworld folders", log_filepath)

        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model_path = os.getenv("ICON_MODEL_PATH", 'C:\\Users\\author_1\\Documents\\GitHub\\bugcraft\\action_model\\OmniParser\\weights\\icon_detect_v1_5\\model_v1_5.pt')
        trajectory = []
        all_trajectory = []
        # Initialize the ImageAnnotator
        annotator = OmniParser(model_path, device=device)
        # Start the macro API in a separate thread
        #macro_thread = threading.Thread(target=macro_run)
        launcher = launch_minecraft(bug_version)
        #macro_thread.daemon = True
        try:
            #macro_thread.start()
            log_message("Threads are ready.", log_filepath)
            log_message("OmniParser is ready.", log_filepath) 
            window_title_prefix = "Minecraft"  # Adjust if needed based on launcher and version
            
            # Wait for the Minecraft window to appear
            minecraft_window = None
            start_time = time.time()
            while minecraft_window is None and time.time() - start_time < 30:  # Wait up to 30 seconds
                for window in pyautogui.getAllWindows():
                    if window.title.startswith(window_title_prefix):
                        minecraft_window = window
                        break
                time.sleep(1)

            if minecraft_window is not None:
                log_message(f"Minecraft window found: {minecraft_window.title}", log_filepath)
                # Maximize the window
                try:
                    if MAKE_FULLSCREEN:
                        minecraft_window.maximize()
                        log_message("Minecraft window maximized.", log_filepath)
                    else:
                        minecraft_window.resizeTo(1366, 768)
                        minecraft_window.moveTo(0, 0)
                except:
                    log_message("Couldnt maximize", log_filepath)

            else:
                log_message("Minecraft window not found within the timeout.", log_filepath)
                return  # Exit the function if the window is not found
            time.sleep(6)
            current_step = 0
            iteration_count = 0
            while launcher.is_minecraft_running():
                iteration_count += 1
                if iteration_count > 30:
                    log_message("Failed - exceeded 30 iterations", log_filepath)
                    launcher.kill_minecraft()
                    break
                trajectory_text = format_iterations(trajectory)
                #log_message(trajectory_text, log_filepath)
                bug_steps_str = str(bug_steps)
                current_step_title = bug_steps[current_step]["title"]
                img_filepath = take_screenshot_of_minecraft_window(issue_name=issue_name, folder_timestamp= beginning_timestamp)
                unannotated_base64 = read_in_base64(img_filepath)
                annotated_image, annotation_list = annotator(img_filepath)
                annotated_filepath = save_screenshot_with_timestamp(annotated_image, issue_name= issue_name, folder_timestamp= beginning_timestamp) #annotation list is not used here when saving
                annotation_table = format_data_as_table(annotation_list)
                log_message(f"Annotation Table:\n{annotation_table}", log_filepath) # Logging the annotation table
                annotated_base64 = read_in_base64(annotated_filepath)
                if SEPERATE_THOUGHT:
                    thought = thought_chain.invoke({"annotation_table": annotation_table,
                                                    "annotated_image_data": annotated_base64,
                                                    "unannotated_image_data": unannotated_base64,
                                                    "step_clusters": bug_steps_str,
                                                    "current_step_title": current_step_title,
                                                    "trajectory": trajectory_text})
                    actions = action_chain.invoke({"annotation_table": annotation_table,
                                                    "annotated_image_data": annotated_base64,
                                                    "step_clusters": bug_steps_str,
                                                    "current_step_title": current_step_title,
                                                    "trajectory": trajectory_text,
                                                    "thought": thought}).command_list
                else:
                    thought_action = thought_action_chain.invoke({"annotation_table": annotation_table,
                                                    "annotated_image_data": annotated_base64,
                                                    "unannotated_image_data": unannotated_base64,
                                                    "step_clusters": bug_steps_str,
                                                    "current_step_title": current_step_title,
                                                    "trajectory": trajectory_text})
                    thought = thought_action.thought
                    actions = thought_action.command_list
                log_message(f"Thought: {thought}", log_filepath)
                log_message(f"Action: {actions}", log_filepath)
                if USE_CORRECTION:
                    feedback_model = self_correction_chain.invoke({"annotation_table": annotation_table,
                                                    "annotated_image_data": annotated_base64,
                                                    "unannotated_image_data": unannotated_base64,
                                                    "step_clusters": bug_steps_str,
                                                    "current_step_title": current_step_title,
                                                    "trajectory": trajectory_text,
                                                    "thought": thought,
                                                    "action": actions})
                    log_message(f"Generated Feedback: {feedback_model}", log_filepath)
                    classification = feedback_model.classification
                    feedback = feedback_model.reasoning
                    if classification == "INCORRECT":
                        thought_action = action_correction_chain.invoke({"annotation_table": annotation_table,
                                                    "annotated_image_data": annotated_base64,
                                                    "unannotated_image_data": unannotated_base64,
                                                    "step_clusters": bug_steps_str,
                                                    "current_step_title": current_step_title,
                                                    "trajectory": trajectory_text,
                                                    "thought": thought,
                                                    "action": actions,
                                                    "feedback": feedback})
                        thought = thought_action.thought
                        actions = thought_action.command_list
                        log_message(f"New Thought: {thought}", log_filepath)
                        log_message(f"New Action: {actions}", log_filepath)

                new_actions = [] #initialize the actions array
                for action in actions:
                    if action.startswith("click_place"):
                        start_index = len("click_place(")
                        end_index = action.find(")")
                        if start_index >= 0 and end_index > start_index:
                            number = int(action[start_index:end_index])
                            if number >= 0 and len(annotation_list) > number:
                                bbox = annotation_list[number]["bbox"]
                                coordinate_x = (bbox[0] + bbox[2]) / 2
                                coordinate_y = (bbox[1] + bbox[3]) / 2
                                new_action = f"click({coordinate_x}, {coordinate_y})"
                                new_actions.append(new_action)
                    else:
                        new_actions.append(action)
                
                actions_annotated = format_commands(actions, annotation_list)

                send_commands_to_macro(new_actions)
                time.sleep(0.3)
                reflection_img_filepath = take_screenshot_of_minecraft_window(issue_name = issue_name, folder_timestamp= beginning_timestamp)
                reflection_base64 = read_in_base64(reflection_img_filepath)
                reflection = reflection_chain.invoke({"image_data": reflection_base64,
                                                "step_clusters": bug_steps_str,
                                                "current_step_title": current_step_title,
                                                "trajectory": trajectory_text,
                                                "thought": thought,
                                                "action": actions_annotated})
                log_message(f"reflection: {reflection}", log_filepath)
                reflection = {"text": reflection.reflection, "classification": reflection.classification}
                trajectory.append({"current_title":current_step_title ,"thought": thought, "action": actions_annotated, "reflection": reflection})
                all_trajectory.append({"current_title":current_step_title ,"thought": thought, "action": actions_annotated, "reflection": reflection})
                if reflection["classification"] == "MOVE_TO_NEXT_CLUSTER":
                    trajectory_text = format_iterations(trajectory)
                    cluster_judgment = cluster_verification_chain.invoke({"image_data": reflection_base64,
                                                "step_clusters": bug_steps_str,
                                                "current_step_title": current_step_title,
                                                "trajectory": trajectory_text,})
                    log_message(f"Move next step judgment: {cluster_judgment}", log_filepath)
                    if cluster_judgment.classification == "CORRECT" and current_step < len(bug_steps) - 1:
                        current_step += 1
                        #trajectory = []
                    else:
                        trajectory[-1]["reflection"]["classification"] = "SUCCESS"
                    if len(bug_steps) <= current_step:
                        log_message("Successfully done, exiting now.", log_filepath)
                        break
                if len(trajectory) >= 25:
                    trajectory = trajectory[1:] #forget last trajectory
            log_message(str(all_trajectory), log_filepath)
            if iteration_count > 30:
                return False
            return True
        except Exception as e:
            log_message(f"Error in ready_apis: {e}", log_filepath)
            raise
    finally:
        if observer:
            observer.stop()
            observer.join()
        
        # Archive the final state of the worlds
        try:
            minecraft_saves = get_minecraft_saves_dir()
            issue_worlds_dir = os.path.join("worlds", issue_name)
            os.makedirs(issue_worlds_dir, exist_ok=True)
            
            # Copy all worlds from minecraft saves to our archive
            if os.path.exists(minecraft_saves):
                for world_name in os.listdir(minecraft_saves):
                    world_path = os.path.join(minecraft_saves, world_name)
                    if os.path.isdir(world_path) and not world_name.endswith('_backup'):
                        target_path = os.path.join(issue_worlds_dir, f"{world_name}_final")
                        if os.path.exists(target_path):
                            shutil.rmtree(target_path)
                        shutil.copytree(world_path, target_path)
                        log_message(f"Archived final world state to {target_path}", log_filepath)
        except Exception as e:
            log_message(f"Error archiving worlds: {e}", log_filepath)
        
        launcher.kill_minecraft()

if __name__ == "__main__":
    ready_apis()
