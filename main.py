import os
import asyncio
import aiohttp
from tqdm import tqdm
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from instaloader import Instaloader, Post
from tiktokapipy.async_api import AsyncTikTokAPI
from tiktokapipy.models.video import Video



VIDEO_DIR = "videos"
FLIC_TOKEN = "flic_e7e97bcd284950823c79e016ea48b4adcd704fe887980997ae68aefac63ec814"  
BASE_API_URL = "https://api.socialverseapp.com"

os.makedirs(VIDEO_DIR, exist_ok=True)

# Retry decorator for failed network requests
def retry(func, retries=3, delay=2):
    async def wrapper(*args, **kwargs):
        for attempt in range(retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                print(f"Error in {func.__name__}, attempt {attempt + 1}/{retries}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
        raise Exception(f"Failed after {retries} retries in {func.__name__}")
    return wrapper

# Utility function to download Instagram video from insta video's url
async def download_instagram_video(url):
    loader = Instaloader(
        download_pictures=False,
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,    
        )
    post = Post.from_shortcode(loader.context, url.split("/")[-2])
    file_path = os.path.join(VIDEO_DIR, f"{post.owner_username}_{post.date_utc.strftime('%Y%m%d')}.mp4")
    loader.download_post(post, target=VIDEO_DIR)
    return file_path

# Utility function to download Tiktok video from Tiktok video's url
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
                        print(f"Video downloaded successfully: {video_path}")
                    else:
                        print(f"Failed to download video. HTTP Status: {resp.status}")
    except Exception as e:
        print(f"Error downloading TikTok video: {e}")

# Async function to get upload URL
@retry
async def get_upload_url():
    url = f"{BASE_API_URL}/posts/generate-upload-url"
    headers = {
        "Flic-Token": FLIC_TOKEN,
        "Content-Type": "application/json",
    }
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

# Async function to upload video
@retry
async def upload_video(file_path, upload_url):
    file_size = os.path.getsize(file_path)
    
    try:
        # Open the file for reading in binary mode
        with open(file_path, "rb") as f:
            # Create a tqdm progress bar
            with tqdm(
                total=file_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=f"Uploading {os.path.basename(file_path)}",
            ) as progress:
                async with aiohttp.ClientSession() as session:
                    # Read and upload the file in chunks
                    chunk_size = 1024 * 1024  # 1 MB per chunk
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:  # End of file
                            break
                        
                        # Make a PUT request for each chunk
                        async with session.put(upload_url, data=chunk) as response:
                            if response.status != 200:
                                print(f"Failed to upload {file_path}: {response.status}")
                                return
                        
                        # Update progress bar with the size of the uploaded chunk
                        progress.update(len(chunk))

        print(f"Uploaded {file_path} successfully.")
    except Exception as e:
        print(f"Error uploading {file_path}: {e}")


@retry
# Async function to create post
async def create_post(title, file_hash, category_id=1):
    url = f"{BASE_API_URL}/posts"
    headers = {
        "Flic-Token": FLIC_TOKEN,
        "Content-Type": "application/json",
    }
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

# File system event handler
class VideoHandler(FileSystemEventHandler):
    def __init__(self, loop):
        self.loop = loop

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".mp4"):
            return

        print(f"New video detected: {event.src_path}")
        # Schedule the coroutine in the event loop
        self.loop.create_task(self.process_file(event.src_path))

    async def process_file(self, file_path):
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


# Directory monitor
async def monitor_directory(loop):
    event_handler = VideoHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, VIDEO_DIR, recursive=False)
    observer.start()

    try:
        with tqdm(desc="Monitoring directory", unit="sec") as progress:
            while True:
                await asyncio.sleep(1)
                progress.update(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


# Main function
async def main():
    print("Starting Video Search and Upload Bot...")

    instagram_url = "https://www.instagram.com/p/C8UZkeZxT6C/" 
    tiktok_url = "https://www.tiktok.com/@subhamshukla3/video/6984779556016213275?lang=en" 

    print("Downloading Instagram video...")
    try:
       await download_instagram_video(instagram_url)
    except Exception as e:
        print(f"Error downloading Instagram video: {e}")
    
    print("Downloading TikTok video...")
    try:
        await download_tiktok_video(tiktok_url)
    except Exception as e:
        print(f"Error downloading TikTok video: {e}")


    print("Monitoring directory for new videos...")
    loop = asyncio.get_event_loop()
    await monitor_directory(loop)


if __name__ == "__main__":
    asyncio.run(main())