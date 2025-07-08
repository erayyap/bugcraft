import os
from dotenv import load_dotenv

load_dotenv()

def str_to_bool(value: str) -> bool:
    """Convert truthy strings to boolean"""
    return str(value).lower() in ("yes", "true", "t", "1", "y")

# Configuration settings
WIKI_DIRECTORY = os.getenv(
    "WIKI_DIRECTORY", 
    r"C:\Users\YOUR_USERNAME\Documents\GitHub\bugcraft\bugcraft\wiki\output_pages"
)

# Convert environment variables using the helper function
USE_WIKI = str_to_bool(os.getenv("USE_WIKI", "True"))
USE_SEARCH = str_to_bool(os.getenv("USE_SEARCH", "False"))
USE_MOB_CHECKER = str_to_bool(os.getenv("USE_MOB_CHECKER", "True"))
USE_REASONING_TRAJECTORY = str_to_bool(os.getenv("USE_REASONING_TRAJECTORY", "True"))
USE_ALTERNATE_SOLUTIONS = str_to_bool(os.getenv("USE_ALTERNATE_SOLUTIONS", "False"))
USE_FINAL_CLUSTERING = str_to_bool(os.getenv("USE_FINAL_CLUSTERING", "False"))

# Numerical values
JUDGE_THRESHOLD = 7
SOURCE_MAX_ITERATION = 1

# Model configuration
MODEL_NAME = os.getenv("STEP_SYNTH_MODEL_NAME", "gpt-4o")