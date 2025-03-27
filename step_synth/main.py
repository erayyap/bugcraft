#TODO: dont touch this file

from fastapi import FastAPI, File, UploadFile, Request, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
import threading
import tempfile
import os
import uuid

# Assuming these are your custom modules (make sure they are in the correct path)
from step_synth.environment import (
    WIKI_DIRECTORY,
    USE_WIKI,
    USE_SEARCH,
    USE_FINAL_CLUSTERING,
)
from step_synth.analyze import (
    process_wiki,
    search_iterations,
    generate_s2r,
    enhance_s2r,
    process_clusters,
    refine_clusters,
    evaluate_images,
    evaluate_videos,
    final_clustering
)
from step_synth.logger import logger
from step_synth.utils import get_filenames_from_folder
# Initialize the FastAPI application
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FileProcessorAPI:
    def __init__(self, app: FastAPI):
        self.app = app  # Correctly references the passed app instance
        self.filenames = get_filenames_from_folder(WIKI_DIRECTORY)
        self.staged_files = {}  # Dictionary to store staged files
        self.app.post("/upload/")(self.upload_files)
        self.app.post("/stage-files/")(self.stage_files)
        self.app.get("/media/{file_code}")(self.serve_media)

    def process_files(
        self,
        video_codes: Optional[List[str]],
        image_codes: Optional[List[str]],
        description: Optional[str],
        version: Optional[str],
        config: Dict[str, str],
    ):
        all_results = []
        if USE_WIKI:
            logger.log("Wiki RAG is being done.")
            wiki_results = process_wiki(description, version, self.filenames)
            all_results += wiki_results

        if USE_SEARCH:
            logger.log("Search tool is being used.")
            search_results = search_iterations(description, wiki_results)
            logger.log(f"Search results processed: {search_results}")
            all_results += search_results

        s2r = generate_s2r(description, all_results)
        enhanced_s2r = enhance_s2r(s2r, all_results)
        s2r = enhanced_s2r  # Update s2r with the enhanced version

        clusters = process_clusters(s2r)
        clusters = refine_clusters(clusters)

        # Pass self.staged_files to the evaluation functions
        image_datas = evaluate_images(
            clusters, all_results, image_codes, self.staged_files
        )
        video_datas = evaluate_videos(
            clusters, all_results, video_codes, self.staged_files
        )
        if USE_FINAL_CLUSTERING:
            final_clustering(clusters, image_datas, video_datas)
        logger.log("Bug report analyzed.", "end")

    async def stage_files(self, files: List[UploadFile] = File(...)):
        """
        Stages uploaded files and uses the provided codes as filenames.
        """
        file_codes = {}
        for file in files:
            # Get the original file extension
            file_extension = os.path.splitext(file.filename)[1]

            # Read the content of the file
            file_content = await file.read()

            # Determine if it's an image or video based on extension
            if file_extension.lower() in [".jpg", ".jpeg", ".png", ".gif"]:
                file_code = str(
                    uuid.uuid4()
                )  # Generate a unique code for images
            elif file_extension.lower() in [".mp4", ".avi", ".mov"]:
                file_code = str(
                    uuid.uuid4()
                )  # Generate a unique code for videos
            else:
                file_code = str(uuid.uuid4())  # Handle other file types as needed

            # Create a temporary file with the code as the name and the original extension
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=file_extension, prefix=file_code + "_"
            ) as temp_file:
                temp_file.write(file_content)
                self.staged_files[file_code] = temp_file.name
                file_codes[file.filename] = file_code

        return file_codes

    async def upload_files(self, request: Request):
        """
        Processes staged files based on provided codes.
        """
        try:
            # Get form data from request body
            form_data = await request.json()
            description = form_data.get("description", "")
            version = form_data.get("version", "")
            # Handle both string and list formats for video_codes and image_codes
            video_codes = form_data.get("video_codes", [])
            if isinstance(video_codes, str):
                video_codes = video_codes.split(",") if video_codes else []

            image_codes = form_data.get("image_codes", [])
            if isinstance(image_codes, str):
                image_codes = image_codes.split(",") if image_codes else []

            def event_generator():
                processing_thread = threading.Thread(
                    target=self.process_files,
                    args=(video_codes, image_codes, description, version, {}),
                )
                processing_thread.start()

                for message in logger.stream_messages():
                    yield f"data: {message}\n\n"

                processing_thread.join()

                # Cleanup: Remove staged files after processing
                # For testing let this remain commented.
                """for code in video_codes + image_codes:
                    if code in self.staged_files:
                        os.unlink(self.staged_files[code])
                        del self.staged_files[code]"""

            return StreamingResponse(
                event_generator(), media_type="text/event-stream"
            )
        except Exception as e:
            logger.log(f"Error in upload_files: {e}")
            raise

    async def serve_media(self, file_code: str):
        """
        Serves staged media files.
        """
        if file_code not in self.staged_files:
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(self.staged_files[file_code])

# Create an instance of FileProcessorAPI, passing the app instance
file_processor_api = FileProcessorAPI(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)