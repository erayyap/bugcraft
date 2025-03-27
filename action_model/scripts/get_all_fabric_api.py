import os
import subprocess
import shutil

def run_command(command):
    """Runs a command in the shell and returns the output."""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error while running command: {command}\n{e.stderr}")
        return None

def get_release_info():
    """Fetches the release tags and titles from the GitHub repository."""
    command = "gh release list -R FabricMC/fabric -L 1000"
    output = run_command(command)
    if output:
        releases = []
        for line in output.splitlines():
            # Extract title and tag by splitting the line correctly
            parts = line.rsplit(maxsplit=2)
            if len(parts) > 2:
                title = parts[0].strip()
                tag = parts[-2].strip()
                releases.append((tag, title))
        return releases
    return []

def sanitize_filename(filename):
    """Sanitizes a filename for use on the filesystem."""
    return "".join(c for c in filename if c.isalnum() or c in " ._-()").strip()

def download_releases(releases, download_dir):
    """Downloads each release using the provided tags and renames them to their titles."""
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    for tag, title in releases:
        print(f"Downloading release: {tag}")
        temp_dir = os.path.join(download_dir, "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        command = f"gh release download {tag} -R FabricMC/fabric -D {temp_dir}"
        run_command(command)

        # Rename files to match the sanitized title
        for file_name in os.listdir(temp_dir):
            old_path = os.path.join(temp_dir, file_name)
            sanitized_title = sanitize_filename(title)
            new_path = os.path.join(download_dir, f"{sanitized_title}{os.path.splitext(file_name)[1]}")
            shutil.move(old_path, new_path)

        os.rmdir(temp_dir)

def main():
    download_dir = "fabric_apis"
    print("Fetching release tags and titles...")
    releases = get_release_info()

    if not releases:
        print("No releases found or an error occurred.")
        return

    print(f"Found {len(releases)} releases. Starting download...")
    download_releases(releases, download_dir)
    print("Download and renaming complete.")

if __name__ == "__main__":
    main()
