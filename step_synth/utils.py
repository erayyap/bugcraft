import os
import re
import base64
from moviepy.video.io.VideoFileClip import VideoFileClip
from PIL import Image
import io
from datetime import datetime, timedelta

def get_filenames_from_folder(folder_path):
    """
    Traverse a folder and save all filenames (without extensions) into an array.
    """
    filenames = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            filename, _ = os.path.splitext(file)  # Separate filename and extension
            filenames.append(filename)
    return filenames

def is_within_one_damerau_levenshtein(s1, s2):
    """
    Check if two strings are within one Damerau-Levenshtein distance,
    considering substitutions, insertions/deletions, and transpositions.
    """
    if s1 == s2:
        return True
    if abs(len(s1) - len(s2)) > 1:
        return False

    len1, len2 = len(s1), len(s2)

    if len1 == len2:
        # Check for substitution or transposition
        mismatches = []
        for i in range(len1):
            if s1[i] != s2[i]:
                mismatches.append(i)
                if len(mismatches) > 2:
                    return False
        if len(mismatches) == 1:
            # One substitution
            return True
        elif len(mismatches) == 2:
            # Possible transposition
            i, j = mismatches
            if i + 1 == j and s1[i] == s2[j] and s1[j] == s2[i]:
                return True
            else:
                return False
        else:
            return False
    else:
        # Check for insertion/deletion
        # Ensure s1 is the shorter string
        if len1 > len2:
            s1, s2 = s2, s1
            len1, len2 = len2, len1
        # Now len2 == len1 + 1
        i = j = 0
        mismatch_found = False
        while i < len1 and j < len2:
            if s1[i] == s2[j]:
                i += 1
                j += 1
            else:
                if mismatch_found:
                    return False
                mismatch_found = True
                j += 1  # Skip a character in the longer string
        return True

def normalize(s):
    """
    Normalize a string by converting it to lowercase and removing non-alphanumeric characters.
    """
    return re.sub(r'\W+', '', s.lower())


def read_files(base_directory, file_names):
    # Ensure the base directory ends with a slash
    if not base_directory.endswith('/'):
        base_directory += '/'
    
    # Store file contents in an array
    file_objects = []
    
    for file_name in file_names:
        file_path = os.path.join(base_directory, f"{file_name}.txt")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding="utf-8") as file:
                file_objects.append({"title": file_name, "text": file.read()})
        else:
            print(f"File not found: {file_path}")
    
    return file_objects
def find_media_files(folder_path, picture_extensions, video_extensions):
    """
    Finds all image and video files in a folder and returns them as two separate arrays.

    Parameters:
        folder_path (str): The path to the folder to search.
        picture_extensions (list): List of image file extensions (e.g., ['.jpg', '.jpeg']).
        video_extensions (list): List of video file extensions (e.g., ['.mp4', '.avi']).

    Returns:
        tuple: Two lists - one with image file paths, and the other with video file paths.
    """
    # Ensure extensions are lowercase for case-insensitive matching
    picture_extensions = [ext.lower() for ext in picture_extensions]
    video_extensions = [ext.lower() for ext in video_extensions]

    image_files = []
    video_files = []

    # Walk through the directory
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()

            if file_ext in picture_extensions:
                image_files.append(file_path)
            elif file_ext in video_extensions:
                video_files.append(file_path)

    return image_files, video_files

def get_first_frames_each_second_as_base64(video_path):
    """
    Given a video file path, returns a list of dictionaries containing
    Base64-encoded strings for the first frame of each second and the last
    frame of the video, along with their corresponding timestamps.

    :param video_path: Path to the video file.
    :return: List of dictionaries with 'base64' and 'timestamp' keys.
    """
    # Load the video clip
    clip = VideoFileClip(video_path)
    duration = int(clip.duration)  # Total duration in seconds
    base64_frames = []

    def frame_to_base64(frame):
        """
        Converts a NumPy array (frame) to a Base64-encoded string.
        """
        # Convert the frame to a PIL image
        image = Image.fromarray(frame)
        # Save the image to a BytesIO buffer
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        # Encode the image in Base64
        return base64.b64encode(buffer.read()).decode('utf-8')

    def seconds_to_timecode(seconds):
        """
        Converts seconds to a time code string in "HH:MM:SS" format.
        """
        return str(timedelta(seconds=int(seconds))).zfill(8)

    # Extract the first frame of each second and convert to Base64
    for t in range(0, duration):
        frame = clip.get_frame(t)
        timecode = seconds_to_timecode(t)
        base64_frames.append({
            'base64': frame_to_base64(frame),
            'timestamp': timecode
        })

    # Extract the last frame of the video and convert to Base64
    last_t = clip.duration
    last_frame = clip.get_frame(last_t)
    last_timecode = seconds_to_timecode(last_t)
    base64_frames.append({
        'base64': frame_to_base64(last_frame),
        'timestamp': last_timecode
    })

    # Close the video clip to release resources
    clip.close()

    return base64_frames

def find_matches(array, main_string):
    """
    Find which phrases in the array are present in the main string with a fuzzy matching
    of maximum edit distance 1 (including transpositions), ignoring case.
    """
    # Tokenize the main string into words
    main_words = re.findall(r'\w+', main_string.lower())

    # Generate all possible substrings (contiguous sequences of words) from the main string
    substrings = []
    for i in range(len(main_words)):
        for j in range(i + 1, len(main_words) + 1):
            substr = ' '.join(main_words[i:j])
            substrings.append(substr)

    # Normalize substrings for comparison
    normalized_substrings = [normalize(s) for s in substrings]

    # Initialize a set to store matches
    matches = set()

    # Normalize phrases in the array
    normalized_phrases = [(phrase, normalize(phrase)) for phrase in array]

    # Compare each normalized phrase with normalized substrings
    for original_phrase, norm_phrase in normalized_phrases:
        for norm_substr in normalized_substrings:
            if is_within_one_damerau_levenshtein(norm_phrase, norm_substr):
                matches.add(original_phrase)
                break  # Stop searching after finding a match

    return matches

def array_to_dict(arr):
    if type(arr) is dict:
        return arr
    return {i+1: arr[i] for i in range(len(arr))}

def prepare_br(bug_report, content):
    content_str = str(array_to_dict(content))
    if len(content_str) > 4:
        return str(bug_report) + "\nWEB CONTENT:\n" + content_str
    return str(bug_report)

def selection_to_dict(selection):
    return {"annotation": selection.annotation , "reasoning": selection.reasoning, "conclusion": selection.conclusion}

def remove_backslashes(step_clusters):
    fixed_clusters_dict = {}
    for key, cluster in step_clusters.items():
        fixed_cluster = {
            "title": cluster["title"],
            "steps": []
        }
        for step in cluster["steps"]:
            fixed_step = step.replace('\"', '"').replace('\\"', '"').replace("\'", "'").replace("\\'", "'")
            fixed_cluster["steps"].append(fixed_step)
        fixed_clusters_dict[key] = fixed_cluster
    return fixed_clusters_dict