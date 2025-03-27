from step_synth.cli import FileProcessor
from action_model.action_model_agent import ready_apis
from backtrace import backtrace
from action_model.macro_api import run_api as macro_run
import os
import threading
import re
import traceback  # Added import
from action_model.minecraft_runner import kill_all_processes_except_cmd_python
import argparse
import json
from dotenv import load_dotenv

load_dotenv()
#query : project = "Minecraft: Java Edition" AND (cf[11901] = Crash ) AND ("Confirmation Status" = Confirmed OR "Confirmation Status" = "Community Consensus" ) AND resolution = Fixed 

def convert_version_string(version_string):
    """Converts a version string from a format like "1.16 Pre-release 2" to "1.16-pre2".
    Also converts "1.16 Release Candidate 1" to "1.16-rc1".

    Args:
        version_string: The version string to convert.

    Returns:
        The converted version string, or the original string if it doesn't match the expected pattern.
    """
    if version_string == "1.14.1 Pre-Release 1":
        return "1.14.1 Pre-Release 1"
    
    # Check for Pre-release pattern
    pre_release_match = re.match(
        r"(\d+(?:\.\d+)+) [Pp]re-[Rr]elease (\d+)",
        version_string
    )
    if pre_release_match:
        return f"{pre_release_match.group(1)}-pre{pre_release_match.group(2)}"
    
    # Check for Release Candidate pattern
    release_candidate_match = re.match(
        r"(\d+(?:\.\d+)+) [Rr]elease [Cc]andidate (\d+)",
        version_string
    )
    if release_candidate_match:
        return f"{release_candidate_match.group(1)}-rc{release_candidate_match.group(2)}"
    
    return version_string

def find_issue_json_files(root_folder):
    """
    Finds all issue.json files within issue folders under the root folder.

    Args:
        root_folder: The path to the root folder (e.g., "bug_reports").

    Returns:
        A tuple containing:
        - A list of absolute paths to issue.json files
        - A dictionary mapping each issue.json path to a list of full file paths in its directory
    """
    # DONE: add way to get the filenames here for each folder.
    json_files = []
    dir_contents = {}
    for dirpath, dirnames, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename == "issue.json":
                json_path = os.path.abspath(os.path.join(dirpath, filename))
                json_files.append(json_path)
                # Store all file paths in this directory (excluding issue.json itself)
                dir_contents[json_path] = [
                    os.path.abspath(os.path.join(dirpath, f)) 
                    for f in filenames 
                    if f != "issue.json"
                ]
    
    print(f"Found issue.json files: {json_files}")
    return json_files, dir_contents

def dict_to_array(data):
  """Converts a dictionary with numerical keys to a sorted array.

  Args:
    data: A dictionary where keys are integers and values are dictionaries 
          with 'title' and 'steps' keys.

  Returns:
    A list of dictionaries, sorted by the original dictionary's keys. 
    Each dictionary in the list has 'id', 'title', and 'steps' keys.
  """
  result = []
  for key in sorted(data.keys()):
    result.append({
        "title": data[key]["title"],
        "steps": data[key]["steps"],
    })
  return result

def main():
    parser = argparse.ArgumentParser(description="Process bug reports and optionally execute steps.")
    parser.add_argument("--only-step", action="store_true", help="Only perform step extraction, do not execute steps.")
    args = parser.parse_args()

    macro_thread = threading.Thread(target=macro_run)
    macro_thread.daemon = True
    macro_thread.start()
    
    all_success = 0
    file_processor_errors = 0
    analyze_errors = 0
    ready_apis_errors = 0
    issue_jsons, dir_contents = find_issue_json_files("./bug_reports")
    print(f"Number of issue.json files found: {len(issue_jsons)}")
    file_processor = FileProcessor()
    log_data = []

    for issue_json in issue_jsons:
        try:
            change_id, final_state, comments, attachments = backtrace(issue_json, None, None, True)
            title = final_state["summary"]
            description = final_state["description"]
            version = final_state["versions"][0]["name"].removeprefix("Minecraft").strip()
            new_comments = []
            for comment in comments:
                new_comments.append(comment["body"])
            bug_description = f"Version: {version}\nTitle: {title}\nDescription: {description}"
            for i, comment in enumerate(new_comments):
                bug_description += f"\nComment {i + 1}: {comment}\n"
            try:
                print(f"Processing: {issue_json}")
                print(bug_description)
                file_paths = dir_contents[issue_json]
                print(f"Processing files: {file_paths}")
                
                step_clusters = file_processor.analyze(None, bug_description, version, None, None, None)
                step_clusters = dict_to_array(step_clusters)
                print(f"Step clusters: {step_clusters}")

                log_data.append({
                    "issue-json": issue_json,
                    "bug_description": bug_description,
                    "step_clusters": step_clusters,
                    "worlds": file_processor.current_worlds,
                    "datapacks": file_processor.current_datapacks
                })

            except Exception as e:
                analyze_errors += 1
                error_trace = traceback.format_exc()  # Get full stack trace
                print(f"Error in file_processor.analyze for {issue_json}:\n{error_trace}")
                with open("error_counts.txt", "a") as f:
                    f.write(f"Error in file_processor.analyze for {issue_json}:\n{error_trace}\n")
                continue

            if not args.only_step:
                try:
                    release_version = convert_version_string(version)
                    issue_name = os.path.basename(os.path.dirname(issue_json))
                    success = ready_apis(
                        step_clusters, 
                        release_version,
                        issue_name,
                        worlds=None,
                        datapacks=None
                    )
                    if success:
                        all_success += 1
                except Exception as e:
                    ready_apis_errors += 1
                    error_trace = traceback.format_exc()  # Get full stack trace
                    print(f"Error in ready_apis for {issue_json}:\n{error_trace}")
                    with open("error_counts.txt", "a") as f:
                        f.write(f"Error in ready_apis for {issue_json}:\n{error_trace}\n")
                kill_all_processes_except_cmd_python()
        except Exception as e:
            file_processor_errors += 1
            error_trace = traceback.format_exc()  # Get full stack trace
            print(f"Error processing {issue_json}:\n{error_trace}")
            with open("error_counts.txt", "a") as f:
                f.write(f"Error processing {issue_json}:\n{error_trace}\n")

    print(f"Total successes: {all_success}")
    print(f"Total file processing errors: {file_processor_errors}")
    print(f"Total analyze errors: {analyze_errors}")
    print(f"Total ready_apis errors: {ready_apis_errors}")

    with open("error_counts.txt", "w") as f:
        f.write(f"Total successes: {all_success}\n")
        f.write(f"Total file processing errors: {file_processor_errors}\n")
        f.write(f"Total analyze errors: {analyze_errors}\n")
        f.write(f"Total ready_apis errors: {ready_apis_errors}\n")

    with open("step_clusters_log.json", "w") as f:
        json.dump(log_data, f, indent=4)

if __name__ == "__main__":
    main()