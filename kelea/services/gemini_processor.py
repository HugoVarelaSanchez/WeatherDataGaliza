import os
import re
import tempfile
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.types import FileState

load_dotenv()

class GeminiFileProcessor:
    """
    Service class for processing various file types using Gemini API
    Extracts structured data according to prompt.txt schema
    """

    TEXT_FILES = {"application/pdf", "application/vnd.oasis.opendocument.text", "text/markdown", "text/plain"}
    VIDEO_FILES = {"video/mp4", "video/mpeg", "video/mov", "video/avi", "video/x-flv", "video/mpg", "video/webm", "video/wmv", "video/3gpp"}
    IMAGE_FILES = {"image/png", "image/jpeg", "image/webp", "image/heic", "image/heif"}
    AUDIO_FILES = {"audio/wav", "audio/mp3", "audio/aiff", "audio/aac", "audio/ogg", "audio/flac"}
    SUPPORTED_FILES = TEXT_FILES | VIDEO_FILES | IMAGE_FILES | AUDIO_FILES



    # Regex for detecting a URL
    URL_PATTERN = r"^https?://(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{2,6}(/[-a-zA-Z0-9()@:%_\+.~#?&/=]*)?$"




    def __init__(self):
        """Initialize Gemini client with API key from environment"""
        self.client = genai.Client(api_key=os.getenv("API_GEMINI"))
        self.prompt_path = os.path.join(os.path.dirname(__file__), "prompt.txt")




    def _load_prompt(self):
        """Load the prompt template from file"""
        with open(self.prompt_path, "r") as f:
            return f.read()

    def _get_custom_prompt(self, file_type, base_prompt):
        """Customize prompt based on file type"""
        if file_type in self.VIDEO_FILES:
            return base_prompt + "\n\nFor this video file, also extract:\n- Visual scenes and actions\n- Spoken dialogue or narration\n- On-screen text\n- Audio descriptions"
        elif file_type in self.IMAGE_FILES:
            return base_prompt + "\n\nFor this image file, describe visual elements, text, objects, and context."
        elif file_type in self.AUDIO_FILES:
            return base_prompt + "\n\nFor this audio file, transcribe speech and describe audio content."
        else:
            return base_prompt


    def process_file_from_path(self, file_path: str, mime_type: str, filename: str) -> dict:
        """
        Process a file already saved on disk using Gemini API.

        Args:
            file_path: Absolute or relative path to the file on disk
            mime_type: MIME type of the file
            filename: Original filename (for the returned dict)

        Returns:
            dict: Contains filename, content (extracted data), and mime_type

        Raises:
            ValueError: If file type is not supported
            Exception: If processing fails
        """
        if mime_type not in self.SUPPORTED_FILES:
            raise ValueError(f"Unsupported file type: {mime_type}. Supported types: {', '.join(self.SUPPORTED_FILES)}")

        prompt = self._load_prompt()

        gemini_file = self.client.files.upload(file=file_path, config=types.UploadFileConfig(mime_type=mime_type))

        while gemini_file.state not in (FileState.ACTIVE, FileState.FAILED):
            time.sleep(2.5)
            gemini_file = self.client.files.get(name=gemini_file.name)

        if gemini_file.state == FileState.FAILED:
            raise Exception("File processing failed on Gemini's servers")

        custom_prompt = self._get_custom_prompt(mime_type, prompt)

        response = self.client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[
                types.Part(file_data=types.FileData(file_uri=gemini_file.uri)),
                types.Part(text=custom_prompt)
            ],
            config=types.GenerateContentConfig(
                system_instruction="You are a precise data extraction assistant. Do not summarize; extract facts accurately."
            )
        )

        return {
            "filename": filename,
            "content": response.text,
            "mime_type": mime_type
        }

    def process_file(self, file):
        """
        Process and parse the file using Gemini API.
        Saves to a temporary file, processes it, then cleans up.

        Args:
            file: File object from Flask request

        Returns:
            dict: Contains filename, content (extracted data), and mime_type

        Raises:
            ValueError: If file type is not supported
            Exception: If processing fails
        """
        temp_path = None

        try:
            file_type = file.content_type

            ext = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                file.save(temp_file.name)
                temp_path = temp_file.name

            return self.process_file_from_path(temp_path, file_type, file.filename)

        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def validate_url(self, url):
        """
        Validate if the provided URL matches the URL pattern

        Args:
            url: String URL to validate

        Returns:
            bool: True if valid, False otherwise
        """
        return bool(re.match(self.URL_PATTERN, url))
