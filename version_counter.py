import json

def count_unique_versions(json_data):
    """
    Counts the number of unique Minecraft versions found in the given JSON data.

    Args:
        json_data: A list of dictionaries representing bug report data.

    Returns:
        The number of unique Minecraft versions found.
    """

    versions = set()
    for item in json_data:
        description = item["bug_description"]
        # Extract version using string manipulation (find "Version:" and take the substring)
        version_start = description.find("Version:")
        if version_start != -1:
            version_start += len("Version:")
            version_end = description.find("\n", version_start)
            if version_end == -1:
                version_end = len(description)  # If no newline, take the rest of the string
            version = description[version_start:version_end].strip()
            versions.add(version)
    
    return len(versions)

# Load the JSON data from the file
try:
    with open('step_clusters_log.json', 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    print("Error: File 'step_clusters_log.json' not found.")
    exit()  # Exit the script if the file is not found

# Count the unique versions
unique_version_count = count_unique_versions(data)

print(f"Number of unique Minecraft versions found: {unique_version_count}")