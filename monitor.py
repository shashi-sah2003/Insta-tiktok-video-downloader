import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tqdm import tqdm
from upload import process_file 

VIDEO_DIR = "videos"

# Define a class to handle file system events
class VideoHandler(FileSystemEventHandler):
    def __init__(self, loop):
        self.loop = loop

    # Method called when a file is created in the monitored directory
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".mp4"):
            return
        print(f"New video detected: {event.src_path}")
        # Schedule the coroutine in the event loop
        self.loop.create_task(process_file(event.src_path))

# Function to monitor the directory for new video files
async def monitor_directory(loop):
    event_handler = VideoHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, VIDEO_DIR, recursive=False)
    observer.start()
    try:
        # Use tqdm to display a progress bar for monitoring
        with tqdm(desc="Monitoring directory", unit="sec") as progress:
            while True:
                await asyncio.sleep(1)
                progress.update(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

async def main():
    print("Starting Video Monitoring...")
    loop = asyncio.get_event_loop()
    await monitor_directory(loop)

if __name__ == "__main__":
    asyncio.run(main())
