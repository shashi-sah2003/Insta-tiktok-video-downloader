import os
import asyncio
import aiohttp
from tqdm import tqdm
import yt_dlp
from tiktokapipy.async_api import AsyncTikTokAPI
from tiktokapipy.models.video import Video

VIDEO_DIR = "videos"
FLIC_TOKEN = "flic_e7e97bcd284950823c79e016ea48b4adcd704fe887980997ae68aefac63ec814"
BASE_API_URL = "https://api.socialverseapp.com"

os.makedirs(VIDEO_DIR, exist_ok=True)

# A decorator to retry a function up to 3 times with a delay of 2 seconds between attempts.
def retry(func):
    async def wrapper(*args, **kwargs):
        retries = 3
        delay = 2
        for attempt in range(retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                print(f"Error in {func.__name__}, attempt {attempt + 1}/{retries}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
        raise Exception(f"Failed after {retries} retries in {func.__name__}")
    return wrapper

# Manually triggers a watchdog event for a given file path.
async def trigger_watchdog_event(file_path):
    print(f"Triggering watchdog event for: {file_path}")
    await process_file(file_path)

# Downloads an Instagram video from the given URL and saves it to the video directory.
async def download_instagram_video(url):
    ydl_opts = {
        'outtmpl': os.path.join(VIDEO_DIR, '%(id)s.%(ext)s'),
        'format': 'bestvideo',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_file = os.path.join(VIDEO_DIR, f"{info_dict['id']}.mp4")
        return video_file

# Downloads a TikTok video from the given URL and saves it to the video directory.
async def download_tiktok_video(video_url):
    try:
        async with AsyncTikTokAPI() as api:
            video: Video = await api.video(video_url)
            async with aiohttp.ClientSession() as session:
                async with session.get(video.video.download_addr) as resp:
                    if resp.status == 200:
                        video_data = await resp.read()
                        video_path = os.path.join(VIDEO_DIR, f"{video.id}.mp4")
                        with open(video_path, 'wb') as f:
                            f.write(video_data)
                        # print(f"Video downloaded successfully: {video_path}")
                    else:
                        print(f"Failed to download video. HTTP Status: {resp.status}")
    except Exception as e:
        print(f"Error downloading TikTok video: {e}")

# Fetches an upload URL from the server.
@retry
async def get_upload_url():
    url = f"{BASE_API_URL}/posts/generate-upload-url"
    headers = {"Flic-Token": FLIC_TOKEN, "Content-Type": "application/json"}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error fetching upload URL: {response.status}")
        except aiohttp.ClientError as e:
            print(f"Network error during get_upload_url: {e}")
            return None

# Uploads a video file to the server using the provided upload URL.
@retry
async def upload_video(file_path, upload_url):
    file_size = os.path.getsize(file_path)
    
    try:
        with open(file_path, "rb") as f:
            with tqdm(total=file_size, unit="B", unit_scale=True) as progress:
                async with aiohttp.ClientSession() as session:
                    chunk_size = 1024 * 1024  # 1 MB per chunk
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:  # End of file
                            break
                        async with session.put(upload_url, data=chunk) as response:
                            if response.status != 200:
                                print(f"Failed to upload {file_path}: {response.status}")
                                return
                        progress.update(len(chunk))
        print(f"Uploaded {file_path} successfully.")
        
    except Exception as e:
        print(f"Error uploading {file_path}: {e}")

# Creates a post on the server with the given title and file hash.
@retry
async def create_post(title, file_hash, category_id=1):
    url = f"{BASE_API_URL}/posts"
    headers = {"Flic-Token": FLIC_TOKEN, "Content-Type": "application/json"}
    
    data = {
        "title": title,
        "hash": file_hash,
        "is_available_in_public_feed": False,
        "category_id": category_id,
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    print(f"Post created for {title}.")
                else:
                    print(f"Failed to create post: {response.status}")
        except aiohttp.ClientError as e:
            print(f"Network error during create_post: {e}")

# Processes a video file by uploading it and creating a post, then deletes the local file.
async def process_file(file_path):
    print(f"Processing video: {file_path}")
    
    # Get upload URL
    upload_info = await get_upload_url()
    
    if not upload_info:
        print(f"Failed to get upload info for {file_path}")
        return
    
    upload_url = upload_info.get("url")
    file_hash = upload_info.get("hash")
    
    # Upload video
    await upload_video(file_path, upload_url)
    
    # Create post
    await create_post(os.path.basename(file_path), file_hash)

    # Delete local file
    try:
        os.remove(file_path)
        print(f"Deleted local file: {file_path}")
    except OSError as e:
        print(f"Error deleting file {file_path}: {e}")

async def main():
    print("Starting Video Download and Upload Bot...")

    instagram_url = "https://www.instagram.com/p/CrABZE9tKB6/?hl=en"
    tiktok_url = "https://www.tiktok.com/@sabbir6846/video/7256817175330032904?lang=en"

    print("Downloading Instagram video...")
    try:
       insta_video_file =  await download_instagram_video(instagram_url)
       await trigger_watchdog_event(insta_video_file)

    except Exception as e:
        print(f"Error downloading Instagram video: {e}")
    
    print("Downloading TikTok video...")
    try:
        await download_tiktok_video(tiktok_url)
    except Exception as e:
        print(f"Error downloading TikTok video: {e}")


if __name__ == "__main__":
    asyncio.run(main())
