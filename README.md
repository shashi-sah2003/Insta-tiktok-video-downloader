
## Directory Structure

```
├── monitor.py            # continuously check for any file changes in the folder videos
├── upload.py             # main utility function consisting of all APIs
├── README.md             # Project documentation
├── requirements.txt      # all the python packages required for this project
```

## Setup Instructions

1. **Clone the Repository:**
    ```sh
    git clone <repository-url>
    cd <repo-name>
    ```

2. **Create a Virtual Environment:**
    ```sh
    python -m venv .venv
    ```

3. **Activate the Virtual Environment:**
    - On Windows:
      ```sh
      .venv\Scripts\activate
      ```
    - On macOS/Linux:
      ```sh
      source .venv/bin/activate
      ```

4. **Install Dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

## Running the Project

To run the project, execute the main script:

```sh
python monitor.py
```
then run on 2nd terminal
```sh
python upload.py
```
