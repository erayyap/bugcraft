from flask import Flask, request, render_template_string
import minecraft_launcher_lib
import subprocess
import os
import uuid
import re

app = Flask(__name__)

def convert_version_string(version_string):
    """Converts version strings to valid format"""
    if version_string == "1.14.1 Pre-Release 1":
        return "1.14.1 Pre-Release 1"
    
    # Pre-release pattern
    pre_release_match = re.match(
        r"(\d+(?:\.\d+)+) [Pp]re-[Rr]elease (\d+)",
        version_string
    )
    if pre_release_match:
        return f"{pre_release_match.group(1)}-pre{pre_release_match.group(2)}"
    
    # Release candidate pattern
    release_candidate_match = re.match(
        r"(\d+(?:\.\d+)+) [Rr]elease [Cc]andidate (\d+)",
        version_string
    )
    if release_candidate_match:
        return f"{release_candidate_match.group(1)}-rc{release_candidate_match.group(2)}"
    
    return version_string

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Minecraft Launcher</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        .form-group { margin-bottom: 20px; }
        input[type="text"] { padding: 8px; width: 200px; }
        button { padding: 8px 20px; background-color: #4CAF50; color: white; border: none; cursor: pointer; }
        .message { padding: 10px; margin-top: 20px; border-radius: 5px; }
        .success { background-color: #dff0d8; color: #3c763d; }
        .error { background-color: #f2dede; color: #a94442; }
    </style>
</head>
<body>
    <h1>Minecraft Version Launcher</h1>
    <form method="POST">
        <div class="form-group">
            <input type="text" name="version" placeholder="Enter Minecraft version" required>
            <button type="submit">Launch</button>
        </div>
    </form>
    {% if message %}
    <div class="message {{ message_class }}">{{ message }}</div>
    {% endif %}
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    message = None
    message_class = None
    
    if request.method == 'POST':
        version = request.form['version']
        converted_version = convert_version_string(version)
        minecraft_directory = minecraft_launcher_lib.utils.get_minecraft_directory()
        
        try:
            minecraft_launcher_lib.install.install_minecraft_version(
                converted_version, 
                minecraft_directory
            )
            
            offline_uuid = str(uuid.uuid4())
            options = {
                "username": "Player",
                "uuid": offline_uuid,
                "token": ""
            }
            
            minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(
                converted_version, 
                minecraft_directory, 
                options
            )
            subprocess.Popen(minecraft_command)
            
            message = f"Launched Minecraft {converted_version} successfully!"
            message_class = "success"
            
        except Exception as e:
            message = f"Error launching {converted_version}: {str(e)}"
            message_class = "error"
    
    return render_template_string(HTML_TEMPLATE, 
                                message=message, 
                                message_class=message_class)

if __name__ == '__main__':
    app.run(debug=True)