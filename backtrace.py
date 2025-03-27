import argparse
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import json
import sys
import os
import traceback

def is_staff_user(username: str) -> bool:
    staff_prefixes = ['[Mod]', '[Mojang]', '[Helper]']
    return any(username.strip().startswith(prefix) for prefix in staff_prefixes)

def find_last_step_before_staff(issue_json: Dict) -> Optional[int]:
    """Find the last step before a staff member's edit."""
    try:
        changelog = issue_json.get('changelog', {}).get('histories', [])
        if not changelog:
            #print("No changelog entries found")
            return None

        # Sort changelog by created time (oldest to newest)
        changelog.sort(key=lambda x: datetime.strptime(x.get('created', '1970-01-01T00:00:00.000+0000'),
                                                       '%Y-%m-%dT%H:%M:%S.%f%z'))

        #print("\nProcessing steps from oldest to newest to find staff edit")
        for i, item in enumerate(changelog):
            author = item.get('author', {}).get('displayName', '')
            created_time = item.get('created', '')
            #print(f"\nChecking step {i + 1}")
            #print(f"Author: {author}")
            #print(f"Time: {created_time}")

            if is_staff_user(author):
                #print(f"\nFound staff edit at step {i + 1} by {author}")
                return max(0, i)

        #print("\nNo staff edits found")
        return len(changelog)  # Return last step if no staff edits found

    except Exception as e:
        #print(f"Error finding staff edit: {str(e)}")
        traceback.print_exc()
        return None

def filter_comments_by_step(issue_json: Dict, step_time: str) -> List[Dict]:
    """Filter comments to keep only those before the specified step time."""
    try:
        comments_container = issue_json.get('fields', {}).get('comment', {})
        if not comments_container:
            #print("\nNo comments container found in issue")
            return []

        comments = comments_container.get('comments', [])
        if not comments:
            #print("\nNo comments found in comments container")
            return []

        if not step_time:
            #print("\nStep 0: No comments included")
            return []

        step_datetime = datetime.strptime(step_time, '%Y-%m-%dT%H:%M:%S.%f%z')
        filtered_comments = []

        #print(f"\nFiltering comments before {step_time}")
        #print(f"Total comments found: {len(comments)}")

        comments.sort(key=lambda x: datetime.strptime(x.get('created', '9999-12-31T23:59:59.999+0000'),
                                                      '%Y-%m-%dT%H:%M:%S.%f%z'))

        for comment in comments:
            comment_time = comment.get('created')
            if not comment_time:
                #print(f"Warning: Comment missing timestamp")
                continue

            try:
                comment_datetime = datetime.strptime(comment_time, '%Y-%m-%dT%H:%M:%S.%f%z')
                if comment_datetime <= step_datetime:
                    author = comment.get('author', {}).get('displayName', 'Unknown')
                    #print(f"Including comment from {comment_time} by {author}")
                    filtered_comments.append(comment)
                else:
                    ""
                    #print(f"Excluding comment from {comment_time} (after step time)")
            except ValueError as e:
                #print(f"Warning: Could not parse comment timestamp: {comment_time}")
                continue

        #print(f"Found {len(filtered_comments)} comments before step time")
        return filtered_comments
    except Exception as e:
        #print(f"Error filtering comments: {str(e)}")
        traceback.print_exc()
        return []

def filter_attachments_by_step(issue_json: Dict, step_time: str) -> List[Dict]:
    """Filter attachments to keep only those added before the specified step time."""
    try:
        attachments = issue_json.get('fields', {}).get('attachment', [])
        if not attachments:
            #print("\nNo attachments found in issue")
            return []

        step_datetime = datetime.strptime(step_time, '%Y-%m-%dT%H:%M:%S.%f%z')
        filtered_attachments = []

        #print(f"\nFiltering attachments before {step_time}")
        #print(f"Total attachments found: {len(attachments)}")

        attachments.sort(key=lambda x: datetime.strptime(x.get('created', '9999-12-31T23:59:59.999+0000'),
                                                         '%Y-%m-%dT%H:%M:%S.%f%z'))

        for attachment in attachments:
            attachment_time = attachment.get('created')
            if not attachment_time:
                #print(f"Warning: Attachment missing timestamp")
                continue

            try:
                attachment_datetime = datetime.strptime(attachment_time, '%Y-%m-%dT%H:%M:%S.%f%z')
                if attachment_datetime <= step_datetime:
                    author = attachment.get('author', {}).get('displayName', 'Unknown')
                    #print(f"Including attachment from {attachment_time} by {author}")
                    filtered_attachments.append(attachment)
                else:
                    ""
                    #print(f"Excluding attachment from {attachment_time} (after step time)")
            except ValueError as e:
                #print(f"Warning: Could not parse attachment timestamp: {attachment_time}")
                continue

        #print(f"Found {len(filtered_attachments)} attachments before step time")
        return filtered_attachments
    except Exception as e:
        #print(f"Error filtering attachments: {str(e)}")
        traceback.print_exc()
        return []

def apply_change_to_state(state: Dict, item: Dict) -> Dict:
    field = item.get('field')
    if not field:
        return state

    new_state = state.copy()

    if item.get('fromString') is not None:
        new_state[field] = item.get('fromString')
        #print(f"Restored field {field} to previous value: {item.get('fromString')}")
    elif item.get('from') is not None:
        new_state[field] = item.get('from')
        #print(f"Restored field {field} to previous ID: {item.get('from')}")
    else:
        new_state.pop(field, None)
        #print(f"Removed field {field}")

    return new_state

def backtrace_steps(issue_json: Dict, target_step: int) -> Tuple[Optional[str], Optional[Dict], List[Dict], List[Dict]]:
    try:
        changelog = issue_json.get('changelog', {}).get('histories', [])
        if not changelog:
            return None, None, [], []

        changelog.sort(key=lambda x: datetime.strptime(x.get('created', '1970-01-01T00:00:00.000+0000'),
                                                       '%Y-%m-%dT%H:%M:%S.%f%z'))
        total_steps = len(changelog)

        """print(f"\nTotal steps: {total_steps}")
        print(f"Target step: {target_step}")"""

        if target_step == 0:
            #print("Getting initial state (step 0)")
            initial_state = issue_json.get('fields', {}).copy()
            for entry in reversed(changelog):
                for item in entry.get('items', []):
                    initial_state = apply_change_to_state(initial_state, item)
            if changelog:
                first_change_time = changelog[0].get('created', '')
                filtered_comments = filter_comments_by_step(issue_json, first_change_time)
                filtered_attachments = filter_attachments_by_step(issue_json, first_change_time)
            else:
                filtered_comments, filtered_attachments = [], []
            return '0', initial_state, filtered_comments, filtered_attachments

        if target_step < 0 or target_step > total_steps:
            #print(f"\nInvalid step number. Total steps: {total_steps}")
            return None, None, [], []

        #print("Starting from most recent state")

        current_state = issue_json.get('fields', {}).copy()
        target_entry = None

        for i, entry in enumerate(reversed(changelog[target_step:])):
        #print(f"\nProcessing step {i+1} of {len(changelog[target_step:])} (Change ID: {entry.get('id')})")
            #print(f"Created: {entry.get('created')}")
            #print(f"Author: {entry.get('author', {}).get('displayName')}\n")

            for item in entry.get('items', []):
                current_state = apply_change_to_state(current_state, item)

            if i == len(changelog[target_step:]) - 1:
                target_entry = entry
                break

        if target_entry:
            filtered_comments = filter_comments_by_step(issue_json, target_entry.get('created', ''))
            filtered_attachments = filter_attachments_by_step(issue_json, target_entry.get('created', ''))

            #print(f"\nComments at this step:")
            for comment in filtered_comments:
                ""
                #print(f"Created: {comment.get('created')}")
                #print(f"Author: {comment.get('author', {}).get('displayName')}")
                #print(f"Content: {comment.get('body')[:100]}...\n")

            #print(f"\nAttachments at this step:")
            for attachment in filtered_attachments:
                ""
                #print(f"Filename: {attachment.get('filename')}")
                #print(f"Created: {attachment.get('created')}")
                #print(f"Author: {attachment.get('author', {}).get('displayName')}")

            return target_entry.get('id'), current_state, filtered_comments, filtered_attachments

        return None, None, [], []
    except Exception as e:
        #print(f"Error in backtrace_steps: {str(e)}")
        traceback.print_exc()
        return None, None, [], []

def export_state(state: Dict, comments: List[Dict], attachments: List[Dict], output_file: str) -> bool:
    try:
        export_data = {
            'fields': state,
            'comments': comments,
            'attachments': attachments,
            'export_time': datetime.now().isoformat()
        }

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        #print(f"\nExported state to: {output_file}")
        return True
    except Exception as e:
        #print(f"Error exporting state: {str(e)}")
        return False

def backtrace(json_file_path: str, step_number: Optional[int] = None, output_file: Optional[str] = None, find_staff: bool = False) -> Tuple[Optional[str], Optional[Dict], Optional[List[Dict]], Optional[List[Dict]]]:
    try:
        with open(json_file_path, 'r', encoding="utf-8") as f:
            data = json.load(f)

        if find_staff:
            step_number = find_last_step_before_staff(data)
            #print(f"\nFound last step before staff edit: {step_number}")

        if step_number is None:
            #print("Error: Must specify either step number or --find-staff")
            return None, None, None, None

        change_id, final_state, comments, attachments = backtrace_steps(data, step_number)

        if change_id and final_state and output_file:
            export_state(final_state, comments, attachments, output_file)

        return change_id, final_state, comments, attachments
    except FileNotFoundError:
        #print(f"Error: File {json_file_path} not found")
        return None, None, None, None
    except json.JSONDecodeError:
        #print(f"Error: File {json_file_path} is not valid JSON")
        return None, None, None, None
    except Exception as e:
        #print(f"Error: An unexpected error occurred: {str(e)}")
        return None, None, None, None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Backtrace issue steps and optionally export state')
    parser.add_argument('json_file', help='Path to the JSON file')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--step', '-s', type=int, help='Step number to backtrace to (0 for initial state)')
    group.add_argument('--find-staff', '-f', action='store_true', help='Find last step before staff edit')
    parser.add_argument('--output', '-o', help='Output JSON file for the final state')

    args = parser.parse_args()

    change_id, final_state, comments, attachments = backtrace(args.json_file, args.step, args.output, args.find_staff)

    if change_id and final_state:
        step_desc = "initial state" if change_id == '0' else f"step {args.step if args.step is not None else 'before staff edit'}"
        #print(f"\nFound state at {step_desc} (Change ID: {change_id})")
        if not args.output:
            #print("\nFinal state:")
            for key, value in final_state.items():
                ""
                #print(f"\n{key}:")
                #print(value)
                #print("\nComments at this step:")
            for comment in (comments or []):
                ""
                a = 1
                #print(f"\nComment by {comment.get('author', {}).get('displayName')} at {comment.get('created')}:")
                #print(comment.get('body', ''))
                #print("\nAttachments at this step:")
            for attachment in (attachments or []):
                ""
                #print(f"\nAttachment: {attachment.get('filename')} by {attachment.get('author', {}).get('displayName')} at {attachment.get('created')}")
