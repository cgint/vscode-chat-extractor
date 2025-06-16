import sqlite3
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .models import Message, Attachment, CodeBlock, ToolOutput

DATABASE_PATH = os.getenv("VSCODE_STATE_DB_PATH")

def get_db_connection() -> Optional[sqlite3.Connection]:
    if not DATABASE_PATH:
        print("Error: VSCODE_STATE_DB_PATH environment variable not set.")
        return None
    
    db_file = Path(DATABASE_PATH)
    if not db_file.exists():
        print(f"Error: Database file not found at {DATABASE_PATH}")
        return None
        
    try:
        conn = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True) # Read-only mode
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def get_composer_ids_with_details() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return []

    composer_data: Dict[str, Dict[str, Any]] = {}
    try:
        cursor = conn.cursor()
        # Query all relevant keys from cursorDiskKV
        # Key format: cursor_bubbleId:COMPOSER_ID:MESSAGE_ID
        query = "SELECT key, value FROM cursorDiskKV WHERE key LIKE 'cursor_bubbleId:%'"
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            key_parts = row["key"].split(':')
            if len(key_parts) < 3:
                continue
            
            composer_id = key_parts[1]
            message_id = key_parts[2]

            if composer_id not in composer_data:
                composer_data[composer_id] = {
                    "id": composer_id,
                    "message_count": 0,
                    "first_message_text": None,
                    "first_message_id": "~" # A string that sorts high
                }
            
            composer_data[composer_id]["message_count"] += 1
            
            try:
                msg_json = json.loads(row["value"])
                msg_text = msg_json.get("text", "")
                # Try to get the first non-empty message text as title
                if msg_text and message_id < composer_data[composer_id]["first_message_id"]:
                    composer_data[composer_id]["first_message_text"] = msg_text
                    composer_data[composer_id]["first_message_id"] = message_id
            except (json.JSONDecodeError, TypeError):
                # If JSON is invalid or value is not bytes/str, skip this message for title
                pass
        
        conn.close()

        result_list = []
        for cid, data in composer_data.items():
            title = data["first_message_text"] or f"Conversation {cid}"
            if len(title) > 70: # Truncate title
                title = title[:67] + "..."
            result_list.append({
                "id": cid,
                "title": title,
                "message_count": data["message_count"]
            })        
        # Sort by ID (composer_id) for consistent listing
        return sorted(result_list, key=lambda x: x["id"])

    except sqlite3.Error as e:
        print(f"Database query error in get_composer_ids_with_details: {e}")
    finally:
        if conn:
            conn.close()
    return []


def _parse_message_content(message_id: str, msg_json: Dict[str, Any]) -> Message:
    sender = "assistant"
    if msg_json.get("type") == 1: # Type 1 is typically user
        sender = "user"
    
    text = msg_json.get("text", "")
    
    attachments: List[Attachment] = []
    code_blocks: List[CodeBlock] = []
    tool_outputs: List[ToolOutput] = []

    # User message attachments
    if sender == "user":
        current_attachment_files = set()
        if "context" in msg_json and "fileSelections" in msg_json["context"]:
            for selection in msg_json["context"].get("fileSelections", []):
                uri = selection.get("uri", {})
                file_path = uri.get("fsPath") or uri.get("path")
                if file_path:
                    name = Path(file_path).name
                    attachments.append(Attachment(type="file_selection", name=name, path=file_path))
                    current_attachment_files.add(name)
        
        for chunk_uri_obj in msg_json.get("attachedFileCodeChunksUris", []):
            file_path = chunk_uri_obj.get("path")
            if file_path:
                name = Path(file_path).name
                if name not in current_attachment_files: # Avoid duplicates if also in fileSelections
                    attachments.append(Attachment(type="code_chunk_uri", name=name, path=file_path))
                    current_attachment_files.add(name)

    # Assistant message content
    elif sender == "assistant":
        for cb_data in msg_json.get("codeBlocks", []):
            uri_path = None
            if "uri" in cb_data and isinstance(cb_data["uri"], dict):
                uri_path = cb_data["uri"].get("path") or cb_data["uri"].get("_fsPath")
            
            code_blocks.append(CodeBlock(
                language=cb_data.get("languageId"),
                content=cb_data.get("content", ""),
                uri_path=uri_path
            ))
        
        for sl_item in msg_json.get("symbolLinks", []):
            try:
                symbol_link = json.loads(sl_item) if isinstance(sl_item, str) else sl_item
                name = symbol_link.get("symbolName", "N/A")
                path = symbol_link.get("relativeWorkspacePath", "N/A")
                attachments.append(Attachment(type="symbol_link", name=name, path=path))
            except (json.JSONDecodeError, TypeError):
                attachments.append(Attachment(type="symbol_link_error", name=str(sl_item)))

    # Tool outputs (can be for user or assistant, check structure)
    if "toolFormerData" in msg_json:
        tfd = msg_json["toolFormerData"]
        tool_name = tfd.get("tool") # Actual tool name/ID might be here
        status = tfd.get("status")
        raw_result = tfd.get("result")
        
        parsed_data: Any = raw_result
        if isinstance(raw_result, str):
            try:
                parsed_data = json.loads(raw_result)
            except json.JSONDecodeError:
                pass # Keep as string if not valid JSON
        
        tool_outputs.append(ToolOutput(tool_name=str(tool_name) if tool_name else None, status=status, data=parsed_data))
    
    # Sometimes tool results are directly in 'interpreterResults' or 'toolResults'
    for res_list_key in ["interpreterResults", "toolResults"]:
        for tool_res in msg_json.get(res_list_key, []):
            tool_name = tool_res.get("toolName") or tool_res.get("name")
            status = tool_res.get("status")
            result_data = tool_res.get("result") or tool_res.get("output") # Check common fields
            tool_outputs.append(ToolOutput(tool_name=tool_name, status=status, data=result_data))


    return Message(
        id=message_id,
        sender=sender,
        text=text,
        attachments=attachments,
        code_blocks=code_blocks,
        tool_outputs=tool_outputs,
        # raw_json_data=msg_json # Optional: include for full data access on frontend if needed
    )


def get_messages_for_composer(composer_id: str) -> List[Message]:
    conn = get_db_connection()
    if not conn:
        return []

    messages: List[Message] = []
    raw_message_data: List[Tuple[str, Dict[str, Any]]] = []

    try:
        cursor = conn.cursor()
        query = f"SELECT key, value FROM cursorDiskKV WHERE key LIKE 'cursor_bubbleId:{composer_id}:%'"
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            key_parts = row["key"].split(':')
            if len(key_parts) < 3:
                continue
            
            message_id_from_key = key_parts[2] # This is the part to sort by
            
            try:
                msg_json = json.loads(row["value"])
                raw_message_data.append((message_id_from_key, msg_json))
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error decoding JSON for key {row['key']}: {e}")
                # Add a placeholder for unparseable messages?
                # messages.append(Message(id=message_id_from_key, sender="system_error", text=f"Error parsing message: {e}", raw_json_data={"error": str(e)}))
        
        # Sort messages by the message_id part of the key
        raw_message_data.sort(key=lambda x: x[0])

        for msg_id, msg_data_json in raw_message_data:
            messages.append(_parse_message_content(msg_id, msg_data_json))
            
    except sqlite3.Error as e:
        print(f"Database query error in get_messages_for_composer: {e}")
    finally:
        if conn:
            conn.close()
    return messages
