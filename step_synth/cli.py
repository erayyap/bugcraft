from typing import List, Optional, Dict
from step_synth.environment import *
from step_synth.analyze import *
from step_synth.utils import *
from step_synth.logger import logger
import threading
import tempfile
import os
import uuid
import zipfile
import shutil
import time
from pathlib import Path

class FileProcessor:
    def __init__(self):
        self.filenames = get_filenames_from_folder(WIKI_DIRECTORY)
        self.staged_files = {}  # Dictionary to store staged files
        
    def verify_world_structure(self, world_path):
        """
        Verify that a directory has the correct structure to be a Minecraft world.
        Does not handle loading, only structure verification.
        """
        if not os.path.exists(os.path.join(world_path, "level.dat")):
            raise Exception(f"Not a valid world - missing level.dat in {world_path}")
        return True

    def verify_datapack_structure(self, datapack_path):
        """
        Verify that a directory has the correct structure to be a datapack.
        Does not handle loading, only structure verification.
        """
        pack_mcmeta = os.path.join(datapack_path, "pack.mcmeta")
        if os.path.isdir(datapack_path) and not os.path.exists(pack_mcmeta):
            raise Exception(f"Not a valid datapack - missing pack.mcmeta in {datapack_path}")
        return True

    def process_files(
        self,
        video_codes: Optional[List[str]],
        image_codes: Optional[List[str]],
        description: Optional[str],
        version: Optional[str],
        config: Dict[str, str],
        file_paths: Optional[List[str]] = None,
    ):
        """
        Process files and generate clusters based on the description and available resources.
        Identifies and validates worlds and datapacks but does not handle loading them.
        
        Args:
            video_codes: List of video file codes
            image_codes: List of image file codes
            description: Bug description text
            version: Minecraft version
            config: Configuration dictionary
            file_paths: List of absolute paths to files in the bug report directory
            
        Returns:
            A tuple containing:
            - clusters: The generated step clusters
            - worlds: List of world paths
            - datapacks: List of datapack paths
        """
        # First extract all archives
        extracted_paths = {}
        archive_extensions = ['.zip', '.rar', '.7z', '.tar', '.gz', '.tar.gz']
        if file_paths:
            for file_path in file_paths:
                # Convert relative path to absolute path (redundant now since we already have absolute paths)
                abs_path = os.path.abspath(file_path)
                if any(file_path.endswith(ext) for ext in archive_extensions):
                    try:
                        extract_dir = os.path.join(tempfile.mkdtemp(), os.path.splitext(file_path)[0])
                        if file_path.endswith('.zip'):
                            with zipfile.ZipFile(abs_path, 'r') as zip_ref:
                                zip_ref.extractall(extract_dir)
                        else:
                            # For other archive types, use shutil which supports various formats
                            shutil.unpack_archive(abs_path, extract_dir)
                        extracted_paths[file_path] = extract_dir
                        logger.log(f"Extracted {file_path} to {extract_dir}")
                    except Exception as e:
                        logger.log(f"Error extracting {file_path}: {e}")

        # Analyze extracted contents and original files for worlds and datapacks
        worlds = []
        datapacks = []
        
        def process_directory(dir_path, is_extracted=False):
            for root, dirs, files in os.walk(dir_path):
                # Check for world (look for level.dat)
                if 'level.dat' in files:
                    # Get the actual world directory (might be the current directory or its parent)
                    world_dir = root
                    try:
                        if self.verify_world_structure(world_dir):
                            worlds.append({
                                'path': world_dir,
                                'is_extracted': is_extracted,
                                'original_zip': next((zip_name for zip_name, extract_path in extracted_paths.items() 
                                                if root.startswith(extract_path)), None)
                            })
                            logger.log(f"Found valid world at {world_dir}")
                    except Exception as e:
                        logger.log(f"Invalid world structure at {world_dir}: {e}")
                
                # Check for datapack (look for pack.mcmeta)
                if 'pack.mcmeta' in files:
                    datapack_dir = os.path.dirname(os.path.join(root, 'pack.mcmeta'))
                    try:
                        if self.verify_datapack_structure(datapack_dir):
                            datapacks.append({
                                'path': datapack_dir,
                                'is_extracted': is_extracted,
                                'original_zip': next((zip_name for zip_name, extract_path in extracted_paths.items() 
                                                if root.startswith(extract_path)), None)
                            })
                            logger.log(f"Found valid datapack at {datapack_dir}")
                    except Exception as e:
                        logger.log(f"Invalid datapack structure at {datapack_dir}: {e}")

        # Process original files
        if file_paths:
            for file_path in file_paths:
                abs_path = os.path.abspath(file_path)
                if os.path.isdir(abs_path):
                    process_directory(abs_path)
                elif os.path.isfile(abs_path) and not file_path.endswith('.zip'):
                    parent_dir = os.path.dirname(abs_path)
                    process_directory(parent_dir)

        # Process extracted contents
        for extract_dir in extracted_paths.values():
            process_directory(extract_dir, True)

        logger.log(f"Found world directories: {[w['path'] for w in worlds]}")
        logger.log(f"Found datapack directories: {[d['path'] for d in datapacks]}")

        # Continue with existing processing
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

        datapack_list = list(set([d['path'] for d in datapacks]))
        s2r = generate_s2r(description, all_results, datapack_list)
        enhanced_s2r = enhance_s2r(s2r, all_results, description)
        s2r = enhanced_s2r

        clusters = process_clusters(s2r)
        clusters = refine_clusters(clusters)
        clusters = remove_backslashes(clusters)

        # Pass self.staged_files to the evaluation functions
        image_datas = evaluate_images(clusters, all_results, image_codes, self.staged_files)
        video_datas = evaluate_videos(clusters, all_results, video_codes, self.staged_files)
        if USE_FINAL_CLUSTERING:
            final_clustering(clusters, image_datas, video_datas)
        logger.log("Bug report analyzed.", "end")

        # Return both clusters and world/datapack paths
        return clusters, [w['path'] for w in worlds], [d['path'] for d in datapacks]

    def stage_files(self, files: List[Dict[str, bytes]]):
        """
        DEPRECATED: This method is no longer used as we now work with files directly on disk.
        Previously used to stage uploaded files from byte content, but now we handle files in their original locations.
        Kept for potential backwards compatibility.
        
        Args:
            files: List of dictionaries containing filename and byte content
        Returns:
            Dictionary mapping original filenames to generated codes
        """
        file_codes = {}
        for file in files:
            filename = file['filename']
            file_content = file['content']

            # Get the original file extension
            file_extension = os.path.splitext(filename)[1]

            # Determine if it's an image or video based on extension
            if file_extension.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                file_code = str(uuid.uuid4())  # Generate a unique code for images
            elif file_extension.lower() in ['.mp4', '.avi', '.mov']:
                file_code = str(uuid.uuid4())  # Generate a unique code for videos
            else:
                file_code = str(uuid.uuid4())  # Handle other file types as needed

            # Create a temporary file with the code as the name and the original extension
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension, prefix=file_code + "_") as temp_file:
                temp_file.write(file_content)
                self.staged_files[file_code] = temp_file.name
                file_codes[filename] = file_code

        return file_codes

    def analyze(
        self,
        files: List[str],  # Changed from Dict[str, bytes] to List[str] to accept filenames
        description: str,
        version: str,
        video_codes: Optional[List[str]] = None,
        image_codes: Optional[List[str]] = None,
        config: Optional[Dict[str, str]] = None
    ):
        """
        Analyzes the provided files and description.
        
        Args:
            files: List of filenames in the bug report directory. These should be paths to files
                  that exist on disk, as we now work with files directly instead of staging them.
            description: Bug description text
            version: Minecraft version
            video_codes: Optional list of video file codes
            image_codes: Optional list of image file codes
            config: Optional configuration dictionary
            
        Returns:
            The generated step clusters
        """
        if video_codes is None:
            video_codes = []
        if image_codes is None:
            image_codes = []
        if config is None:
            config = {}
        #self.current_worlds = []
        #self.current_datapacks = []

        # Process the files with the filenames
        # This will handle extracting zips and identifying worlds/datapacks
        clusters, worlds, datapacks = self.process_files(video_codes, image_codes, description, version, config, files)
        
        # Store the paths for later use in ready_apis
        self.current_worlds = worlds
        self.current_datapacks = datapacks
        
        return clusters
