import os
import re
import sys
import json
from dotenv import load_dotenv
from openai import OpenAI
from src.gen_video import create_video_complete

load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.thucchien.ai")
if not API_KEY:
    print("ERROR: API_KEY chưa được cấu hình. Hãy tạo file .env hoặc export API_KEY trước khi chạy.")
    sys.exit(1)

def main():
    PROMPT_FILE = "prompts/scene.txt"
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        scene_prompt = f.read()
    create_video_complete(
        api_key=API_KEY,
        prompt=scene_prompt,
        image_path=None,
        output_folder = "videos/output"
    )
    
if __name__ == "__main__":
    main()
