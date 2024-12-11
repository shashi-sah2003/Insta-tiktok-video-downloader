# Video Search and Upload Bot

This project is an asynchronous bot that downloads videos from Instagram and TikTok, monitors a directory for new videos, uploads them to a server, and creates posts.

## Features

- Download videos from Instagram and TikTok.
- Monitor a directory for new video files.
- Upload videos to a server.
- Create posts for uploaded videos.

## Requirements

- Python 3.7+
- `aiohttp`
- `instaloader`
- `tiktokapipy`
- `tqdm`
- `watchdog`

## Installation

1. Clone the repository:
    ```sh
    git clone <repository_url>
    cd <repository_directory>
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Set up the `VIDEO_DIR` and `FLIC_TOKEN` in `main.py`:
    ```py
    VIDEO_DIR = "videos"
    FLIC_TOKEN = "your_flic_token_here"
    ```

2. Run the bot:
    ```sh
    python main.py
    ```

## Code Overview

- `main.py`: Contains the main logic for downloading, monitoring, uploading, and creating posts.
- `requirements.txt`: Lists the dependencies required for the project.
- `.gitignore`: Specifies files and directories to be ignored by git.

## Functions and Classes

### `retry`

A decorator to retry a function if it fails.

### `download_instagram_video(url)`

Downloads an Instagram video from the given URL.

### `download_tiktok_video(video_url)`

Downloads a TikTok video from the given URL.

### `get_upload_url()`

Gets the upload URL from the server.

### `upload_video(file_path, upload_url)`

Uploads a video to the server.

### `create_post(title, file_hash, category_id=1)`

Creates a post for the uploaded video.

### `VideoHandler`

A class to handle file system events.

### `monitor_directory(loop)`

Monitors the directory for new video files.

### `main()`

The main function to start the bot.
