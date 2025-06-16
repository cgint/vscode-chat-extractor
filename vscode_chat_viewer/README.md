# VSCode Chat Viewer

A simple web application to browse VSCode chat conversations directly from the `state.vscdb` SQLite file.

## Features

- Lists all conversations found in the database.
- Displays messages for a selected conversation.
- Shows sender (user/assistant), text, attachments, code blocks, and tool outputs.
- Renders Markdown in message text.

## Setup

1.  **Clone the repository (or create the files as described).**

2.  **Install Python 3.11+ and Poetry.**
    (Refer to official Poetry documentation for installation instructions)

3.  **Install dependencies:**
    ```bash
    poetry install
    ```

4.  **Set up the environment variable:**
    Create a `.env` file in the project root (e.g., `vscode_chat_viewer/.env`) with the path to your VSCode `state.vscdb` file:
    ```env
    VSCODE_STATE_DB_PATH="/path/to/your/state.vscdb"
    ```
    Replace `/path/to/your/state.vscdb` with the actual path.
    Common paths:
    - macOS: `~/Library/Application Support/Code/User/globalStorage/state.vscdb`
    - Windows: `C:\Users\<username>\AppData\Roaming\Code\User\globalStorage\state.vscdb`
    - Linux: `~/.config/Code/User/globalStorage/state.vscdb`
    (Note: For VSCode Insiders, the path might be `Code - Insiders` instead of `Code`)

5.  **Download `marked.min.js`:**
    Download `marked.min.js` from a reliable source (e.g., [jsDelivr](https://www.jsdelivr.com/package/npm/marked)) and place it in `vscode_chat_viewer/web/lib/marked.min.js`.

## Running the Application

1.  Ensure your `.env` file is configured correctly.
2.  Run the FastAPI application using Uvicorn:
    ```bash
    poetry run uvicorn app.main:app --reload
    ```
3.  Open your web browser and navigate to `http://127.0.0.1:8000`.

## Project Structure

```
vscode_chat_viewer/
├── app/                     # Python backend code
│   ├── __init__.py
│   ├── main.py              # FastAPI application, API endpoints
│   ├── db_service.py        # Logic for SQLite database interaction
│   └── models.py            # Pydantic models for data structures
├── web/                     # Frontend static files
│   ├── index.html           # Main HTML page
│   ├── style.css            # CSS for styling
│   └── script.js            # JavaScript for frontend logic
│   └── lib/marked.min.js    # Markdown parsing library
├── .env                     # To store the path to state.vscdb (gitignored)
├── .env.example           # Example for .env
├── pyproject.toml         # Python project configuration
└── README.md              # Project README
```
