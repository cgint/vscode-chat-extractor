from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
import os

from . import db_service
from .models import ConversationInfo, ConversationDetail

app = FastAPI(title="VSCode Chat Viewer API")

# Mount static files first, so API routes are checked later
app.mount("/static", StaticFiles(directory="web"), name="static")
app.mount("/lib", StaticFiles(directory="web/lib"), name="lib")


@app.on_event("startup")
async def startup_event():
    db_path = os.getenv("VSCODE_STATE_DB_PATH")
    if not db_path or not os.path.exists(db_path):
        print("\n" + "*"*50)
        print("ERROR: VSCODE_STATE_DB_PATH environment variable is not set or the file does not exist.")
        print("Please set it in a .env file or as an environment variable.")
        print(f"Current value: {db_path}")
        print("Example: VSCODE_STATE_DB_PATH='/path/to/your/state.vscdb'")
        print("The application might not function correctly without it.")
        print("*"*50 + "\n")
    else:
        print(f"Using database: {db_path}")


@app.get("/api/conversations", response_model=List[ConversationInfo])
async def list_conversations():
    """
    Retrieves a list of all available conversations with basic information.
    """
    conversations = db_service.get_composer_ids_with_details()
    if not conversations:
        # Return empty list if no conversations found, not necessarily an error
        return []
    return conversations

@app.get("/api/conversations/{composer_id}", response_model=ConversationDetail)
async def get_conversation_details(composer_id: str):
    """
    Retrieves all messages for a specific conversation.
    """
    messages = db_service.get_messages_for_composer(composer_id)
    if not messages:
        raise HTTPException(status_code=404, detail=f"Conversation with composer_id '{composer_id}' not found or has no messages.")
    return ConversationDetail(id=composer_id, messages=messages)

@app.get("/")
async def read_index():
    return FileResponse('web/index.html')

# If you have other specific routes like /conversations/{id} on the frontend,
# you might need a catch-all for HTML5 mode routing if you use a JS router.
# For this simple app, direct navigation to index.html is fine.
