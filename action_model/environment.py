import os
from dotenv import load_dotenv

load_dotenv()

def str_to_bool(value: str) -> bool:
    """Convert truthy strings to boolean"""
    return str(value).lower() in ("yes", "true", "t", "1", "y")

google_api_key = "WIP"
openai_base_url = "https://api.openai.com/v1"
google_api_base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
url_type = "openai"
if url_type == "openai":
    MODEL_NAME = os.getenv("ACTION_MODEL_NAME")
    BASE_URL = openai_base_url
    #os.environ["OPENAI_API_KEY"] = openai_key
elif url_type == "google":
    print("GoogleGenAI models are not supported at the moment.")
    MODEL_NAME = "gemini-2.0-flash-exp"
    BASE_URL = google_api_base_url
    #os.environ["OPENAI_API_KEY"] = google_api_key

MAKE_FULLSCREEN = str_to_bool(os.getenv("MAKE_FULLSCREEN", "False"))
SEPERATE_THOUGHT = str_to_bool(os.getenv("SEPERATE_THOUGHT", "False"))
USE_CORRECTION = str_to_bool(os.getenv("USE_CORRECTION", "True"))
USE_UNANNOTATED_IMAGES = str_to_bool(os.getenv("USE_ANNOTATED_IMAGES", "False"))