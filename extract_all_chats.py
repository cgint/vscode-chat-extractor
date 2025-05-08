#!/usr/bin/env python3

import sqlite3
import json
import os
import sys

def extract_all_chat_data(db_path, output_dir="all_extracted_chats"):
    """
    Extract all chat data from the VSCode state database
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First extract the aichat.chatdata which contains most of the chat history
    cursor.execute("SELECT value FROM ItemTable WHERE key = 'workbench.panel.aichat.view.aichat.chatdata'")
    result = cursor.fetchone()
    
    if result:
        try:
            chat_data = json.loads(result[0])
            
            # Save the full chat data
            with open(os.path.join(output_dir, "full_chat_data.json"), "w") as f:
                json.dump(chat_data, f, indent=2)
            
            # Extract and save individual chat sessions
            if "tabs" in chat_data:
                for i, tab in enumerate(chat_data["tabs"]):
                    tab_id = tab.get("tabId", f"chat_tab_{i}")
                    
                    # Save each tab as a separate file
                    with open(os.path.join(output_dir, f"chat_tab_{tab_id}.json"), "w") as f:
                        json.dump(tab, f, indent=2)
                    
                    # Extract conversations in a readable format
                    if "bubbles" in tab:
                        conversations = []
                        
                        for bubble in tab["bubbles"]:
                            bubble_type = bubble.get("type", "unknown")
                            content = bubble.get("content", "")
                            message_id = bubble.get("id", "")
                            
                            # Extract message text and metadata
                            message = {
                                "type": bubble_type,
                                "id": message_id,
                                "content": content
                            }
                            
                            # Extract any code blocks or file references
                            if "mentions" in bubble:
                                message["mentions"] = bubble["mentions"]
                            
                            conversations.append(message)
                        
                        # Save the human-readable conversation
                        with open(os.path.join(output_dir, f"conversation_{tab_id}.json"), "w") as f:
                            json.dump(conversations, f, indent=2)
                        
                        # Also save as plain text for easy reading
                        with open(os.path.join(output_dir, f"conversation_{tab_id}.txt"), "w") as f:
                            for msg in conversations:
                                f.write(f"--- {msg['type'].upper()} ---\n")
                                f.write(f"{msg['content']}\n\n")
            
            print(f"Extracted chat data saved to {output_dir}")
        
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"Error decoding chat data: {e}")
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    # Output tables structure to a file
    with open(os.path.join(output_dir, "database_structure.txt"), "w") as f:
        f.write("Database tables and structures:\n\n")
        
        for table in tables:
            table_name = table[0]
            f.write(f"Table: {table_name}\n")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            f.write("Columns:\n")
            for column in columns:
                f.write(f"  - {column[1]} ({column[2]})\n")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            f.write(f"Total rows: {count}\n\n")
    
    # Extract all entries matching 'chat' keyword
    cursor.execute("SELECT key FROM ItemTable WHERE key LIKE '%chat%'")
    chat_keys = cursor.fetchall()
    
    with open(os.path.join(output_dir, "all_chat_related_keys.txt"), "w") as f:
        for key in chat_keys:
            f.write(f"{key[0]}\n")
    
    conn.close()
    print(f"Database structure information saved to {os.path.join(output_dir, 'database_structure.txt')}")
    print(f"All chat-related keys saved to {os.path.join(output_dir, 'all_chat_related_keys.txt')}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_all_chats.py <path_to_state.vscdb> [output_directory]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) >= 3 else "all_extracted_chats"
    
    extract_all_chat_data(db_path, output_dir) 