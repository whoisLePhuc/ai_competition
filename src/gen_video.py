import requests
import re
import subprocess
import json
import base64
import time
import os

def send_request_generate_video(api_key, prompt, image_path=None):
    """Bước 1: Gửi request tạo video"""
    url = "https://api.thucchien.ai/gemini/v1beta/models/veo-3.0-generate-001:predictLongRunning"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    instance = {"prompt": prompt}
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        instance["image"] = {"bytesBase64Encoded": image_data}
    payload = {
        "instances": [instance],
        "parameters": {
            "negativePrompt": "blurry, low quality",
            "aspectRatio": "16:9",
            "resolution": "720p",
            "personGeneration": "allow_all"
        }
    }
    print("Gửi request tạo video...")
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def poll_operation(api_key, operation_name, max_wait=600, check_interval=15):
    """
    Poll để lấy kết quả
    QUAN TRỌNG: URL để poll phải có đầy đủ path của Gemini API
    """
    # Sửa lại URL đúng format
    # Từ: models/veo-3.0-generate-001/operations/4wji3koqr2bs
    # Thành: /gemini/v1beta/models/veo-3.0-generate-001/operations/4wji3koqr2bs
    url = f"https://api.thucchien.ai/gemini/v1beta/{operation_name}"
    headers = {"x-goog-api-key": api_key}
    start_time = time.time()
    print(f"Đang chờ video được tạo...")
    print(f"Polling URL: {url}")
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            # In ra để debug
            print(f"\nResponse status: {response.status_code}")
            print(f"Response: {json.dumps(result, indent=2)[:500]}...")
            # Kiểm tra đã xong chưa
            if result.get("done"):
                if "error" in result:
                    raise Exception(f"Lỗi từ API: {result['error']}")
                print(f"Video đã xong sau {time.time() - start_time:.0f} giây")
                return result
            # Hiển thị progress nếu có
            metadata = result.get("metadata", {})
            progress = metadata.get("progressPercentage", "?")
            print(f"DDang xử lý... Progress: {progress}% ({time.time() - start_time:.0f}s)")
            time.sleep(check_interval)
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response text: {e.response.text}")
            # Thử với URL khác nếu 404
            if e.response.status_code == 404:
                # Thử thêm các biến thể URL
                alt_urls = [
                    f"https://api.thucchien.ai/{operation_name}",
                    f"https://api.thucchien.ai/v1beta/{operation_name}",
                    f"https://api.thucchien.ai/api/v1beta/{operation_name}"
                ]
                print("\nThử các URL thay thế...")
                for alt_url in alt_urls:
                    try:
                        print(f"   Thử: {alt_url}")
                        alt_response = requests.get(alt_url, headers=headers)
                        if alt_response.status_code == 200:
                            print(f"Tìm thấy URL đúng: {alt_url}")
                            url = alt_url  # Cập nhật URL đúng
                            break
                    except:
                        continue
            time.sleep(check_interval)
    raise TimeoutError("Quá thời gian chờ")

def download_with_curl(api_key, operation_name, output_folder="."):
    """Dùng curl để tải video (đơn giản và tin cậy nhất)"""
    # Step 1: Kiểm tra trạng thái operation
    url = f"https://api.thucchien.ai/gemini/v1beta/{operation_name}"
    headers = {"x-goog-api-key": api_key}
    print("🔍 Checking operation...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    result = response.json()
    if not result.get('done'):
        print("Video vẫn đang xử lý")
        return None
    
    # Step 2: Lấy video URI
    video_uri = (
        result
        .get("response", {})
        .get("generateVideoResponse", {})
        .get("generatedSamples", [{}])[0]
        .get("video", {})
        .get("uri")
    )
    if not video_uri:
        print("Không tìm thấy video URI")
        return None

    print("Found video URI")
    # Step 3: Chuẩn bị URL tải video
    match = re.search(r'/files/([^:]+):download\?alt=media', video_uri)
    if match:
        file_id = match.group(1)
        download_url = f"https://api.thucchien.ai/gemini/download/v1beta/files/{file_id}:download?alt=media"
    else:
        download_url = video_uri.replace(
            "https://generativelanguage.googleapis.com/",
            "https://api.thucchien.ai/gemini/"
        )

    # Step 4: Chuẩn bị thư mục output
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, "my_generated_video.mp4")
    print(f"⬇ Đang tải video tới: {output_path}")
    # Step 5: Dùng curl để tải video
    curl_command = [
        'curl',
        download_url,
        '-H', f'x-goog-api-key: {api_key}',
        '--output', output_path,
        '--progress-bar'
    ]
    try:
        subprocess.run(curl_command, check=True)
        print(f"\nĐã lưu video: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"\nLỗi khi tải bằng curl: {e}")
        print("\nThử lại với URL gốc...")
        # Thử lại với URL gốc
        curl_command_original = [
            'curl',
            video_uri,
            '-H', f'x-goog-api-key: {api_key}',
            '--output', output_path,
            '--progress-bar'
        ]
        try:
            subprocess.run(curl_command_original, check=True)
            print(f"\nĐã lưu video: {output_path}")
            return output_path
        except Exception as e2:
            print(f"\nKhông thể tải video: {e2}")
            print("\nThử lệnh curl thủ công:")
            print(f'curl "{video_uri}" -H "x-goog-api-key: {api_key}" --output my_video.mp4')
            return None

def create_video_complete(api_key, prompt, image_path=None, output_folder = "."):
    """Quy trình hoàn chỉnh: Tạo → Poll → Tải"""

    # Bước 1: Gửi request
    result = send_request_generate_video(api_key, prompt, image_path)
    
    # In ra toàn bộ response để debug
    print(f"\nResponse từ API:")
    print(json.dumps(result, indent=2))
    
    operation_name = result.get("name")
    
    if not operation_name:
        raise Exception("Không nhận được operation name")
    
    print(f"\nOperation Name: {operation_name}")
    
    # Lưu operation name
    with open("operation_name.txt", "w") as f:
        f.write(operation_name)
    print(f"💾 Đã lưu operation name vào operation_name.txt")
    
    # Bước 2: Poll kết quả
    try:
        final_result = poll_operation(api_key, operation_name)
    except Exception as e:
        print(f"\nLỗi khi poll: {e}")
        print(f"Bạn có thể poll lại sau bằng cách chạy:")
        print(f"    poll_saved_operation('{api_key}')")
        raise
    
    # Bước 3: Tải video
    download_with_curl(api_key, operation_name, output_folder=".")