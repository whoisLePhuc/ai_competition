import os
import re
import sys
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.thucchien.ai")
if not API_KEY:
    print("ERROR: API_KEY chưa được cấu hình. Hãy tạo file .env hoặc export API_KEY trước khi chạy.")
    sys.exit(1)

def main():
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )
    messages = [
        {
        "role": "system",
        "content": "Bạn là một trợ lý ảo thân thiện, luôn trả lời bằng tiếng Việt, rõ ràng và hữu ích."
        }
    ]
    print("Trợ lý ảo đã sẵn sàng! (gõ 'exit' để thoát)\n")
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            print("End.")
            break
        
        messages.append({"role": "user", "content": user_input})

        try:
            response = client.chat.completions.create(
                model="gemini-2.5-pro",
                messages=messages,
                temperature=0.7
            )
            reply = response.choices[0].message.content.strip()
            print(f"Assistance: {reply}\n")
            messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            print("Lỗi khi gọi API:", e)
            break

if __name__ == "__main__":
    main()
