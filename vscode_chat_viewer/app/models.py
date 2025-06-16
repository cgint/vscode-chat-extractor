from pydantic import BaseModel, Field
from typing import List, Optional, Any

class Attachment(BaseModel):
    type: str  # e.g., "file_selection", "code_chunk_uri", "symbol_link", "code_block_file"
    name: str
    path: Optional[str] = None
    content: Optional[str] = None # For things like file content previews if ever added

class CodeBlock(BaseModel):
    language: Optional[str] = None
    content: str
    uri_path: Optional[str] = None  # path from codeBlock.uri.path if available

class ToolOutput(BaseModel):
    tool_name: Optional[str] = None # e.g., from toolFormerData.tool
    status: Optional[str] = None # e.g., from toolFormerData.status
    data: Any  # Could be string or parsed JSON from toolFormerData.result

class Message(BaseModel):
    id: str  # message_id (the part after the second colon in the key)
    sender: str  # "user" or "assistant"
    text: str
    attachments: List[Attachment] = Field(default_factory=list)
    code_blocks: List[CodeBlock] = Field(default_factory=list)
    tool_outputs: List[ToolOutput] = Field(default_factory=list)
    # raw_json_data: Dict[str, Any] # For debugging or if more fields are needed later

class ConversationInfo(BaseModel):
    id: str  # composer_id
    title: str
    message_count: int
    # last_updated: Optional[str] = None # Could be ISO format string

class ConversationDetail(BaseModel):
    id: str  # composer_id
    messages: List[Message]
