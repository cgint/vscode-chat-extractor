#!/usr/bin/env python3

import sqlite3
import json
import os
import sys
from datetime import datetime

def dump_sqlite_db(db_path, output_dir="sqlite_dump"):
    """
    Dump all content from the SQLite database into text files for easy searching.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{output_dir}_{timestamp}"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    
    print(f"Found {len(tables)} tables: {', '.join(tables)}")
    
    # Create a directory for each table
    for table in tables:
        table_dir = os.path.join(output_dir, table)
        if not os.path.exists(table_dir):
            os.makedirs(table_dir)
            
        print(f"\nDumping table: {table}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) as count FROM {table};")
        row_count = cursor.fetchone()['count']
        print(f"  Table has {row_count} rows")
        
        # Save all raw data for full-text search
        all_raw_data_file = os.path.join(output_dir, f"all_raw_{table}_data.txt")
        with open(all_raw_data_file, "w", encoding="utf-8") as f:
            cursor.execute(f"SELECT * FROM {table}")
            for row in cursor.fetchall():
                for key in row.keys():
                    if not isinstance(row[key], bytes):
                        f.write(f"{key}: {row[key]}\n")
                    else:
                        # Try to decode as UTF-8
                        try:
                            text_value = row[key].decode('utf-8', errors='ignore')
                            f.write(f"{key}: {text_value}\n")
                        except:
                            pass
                f.write("\n---\n\n")
        
        # Get all rows
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        
        # Save table structure
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        schema = []
        for col in columns:
            schema.append({
                "cid": col["cid"],
                "name": col["name"],
                "type": col["type"],
                "notnull": col["notnull"],
                "default_value": col["dflt_value"],
                "pk": col["pk"]
            })
            
        with open(os.path.join(table_dir, "00_schema.json"), "w") as f:
            json.dump(schema, f, indent=2)
            
        # Save a list of all keys for reference
        if 'key' in schema[0]['name']:
            with open(os.path.join(table_dir, "01_all_keys.txt"), "w") as f:
                for row in rows:
                    f.write(f"{row['key']}\n")
        
        # Process each row
        for i, row in enumerate(rows):
            # Create JSON of row metadata
            row_meta = {}
            for key in row.keys():
                if isinstance(row[key], bytes):
                    row_meta[key] = f"<BINARY DATA: {len(row[key])} bytes>"
                else:
                    row_meta[key] = row[key]
            
            # Use key as filename if available, otherwise use row number
            if 'key' in row.keys():
                safe_key = str(row['key']).replace('/', '_').replace('\\', '_').replace('.', '_')
                if len(safe_key) > 100:  # Truncate very long keys
                    safe_key = safe_key[:100]
                base_filename = f"{safe_key}"
            else:
                base_filename = f"row_{i:05d}"
                
            # Save row metadata
            meta_file = os.path.join(table_dir, f"{base_filename}_meta.json")
            with open(meta_file, "w") as f:
                json.dump(row_meta, f, indent=2)
                
            # Process binary data if present
            for key in row.keys():
                if isinstance(row[key], bytes):
                    # Save raw binary
                    binary_file = os.path.join(table_dir, f"{base_filename}_{key}.bin")
                    with open(binary_file, "wb") as f:
                        f.write(row[key])
                    
                    # Try to decode as text
                    try:
                        text_value = row[key].decode('utf-8', errors='ignore')
                        text_file = os.path.join(table_dir, f"{base_filename}_{key}.txt")
                        with open(text_file, "w", encoding="utf-8") as f:
                            f.write(text_value)
                    except:
                        pass
                    
                    # Try to decode as JSON
                    try:
                        json_data = json.loads(row[key])
                        json_file = os.path.join(table_dir, f"{base_filename}_{key}.json")
                        with open(json_file, "w", encoding="utf-8") as f:
                            json.dump(json_data, f, indent=2)
                    except:
                        pass
                        
                    # Search for any mentions of chats, nodes, conversations in binary data
                    search_terms = [
                        "node demo.js departures", 
                        "chat", 
                        "conversation", 
                        "message",
                        "assistant",
                        "user",
                        "bubbles"
                    ]
                    
                    for term in search_terms:
                        if term.encode('utf-8') in row[key]:
                            match_file = os.path.join(output_dir, f"matches_{term.replace(' ', '_')}.txt")
                            with open(match_file, "a", encoding="utf-8") as f:
                                f.write(f"Match in {table}.{row['key'] if 'key' in row.keys() else f'row_{i}'}\n")
                                f.write(f"File: {os.path.join(table_dir, f'{base_filename}_{key}.txt')}\n\n")
    
    # Create an index file listing all matches
    with open(os.path.join(output_dir, "index.html"), "w") as f:
        f.write("<html><head><title>SQLite Database Dump</title></head><body>\n")
        f.write("<h1>SQLite Database Dump</h1>\n")
        
        # List all match files
        f.write("<h2>Search Term Matches</h2>\n")
        f.write("<ul>\n")
        for filename in os.listdir(output_dir):
            if filename.startswith("matches_"):
                term = filename[8:-4].replace('_', ' ')
                f.write(f"<li><a href='{filename}'>{term}</a></li>\n")
        f.write("</ul>\n")
        
        # List all tables
        for table in tables:
            f.write(f"<h2>Table: {table}</h2>\n")
            f.write("<ul>\n")
            
            # List all keys if available
            keys_file = os.path.join(table, "01_all_keys.txt")
            if os.path.exists(os.path.join(output_dir, keys_file)):
                with open(os.path.join(output_dir, keys_file), "r") as keys:
                    for key in keys:
                        key = key.strip()
                        if key:
                            f.write(f"<li>{key}</li>\n")
            
            f.write("</ul>\n")
        
        f.write("</body></html>\n")
        
    conn.close()
    print(f"\nDatabase dump complete. All files saved to {output_dir}")
    print("You can now search through the text files for your content.")
    print(f"Try: grep -r 'your search term' {output_dir}/")

def extract_chats(db_path, output_dir="extracted_chats"):
    """
    Extract chat history from the database into a more readable format
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # First try to extract chat data from ItemTable
    cursor.execute("SELECT key, value FROM ItemTable WHERE key LIKE '%chat%' OR key LIKE '%bubbles%' OR key LIKE '%conversation%'")
    chat_related_rows = cursor.fetchall()
    
    extracted_chats = []
    
    for key, value in chat_related_rows:
        # Skip if value is None
        if value is None:
            print(f"Skipping {key} with None value")
            continue
            
        try:
            # Try to decode as JSON
            json_data = json.loads(value)
            
            # Save as JSON file
            json_file = os.path.join(output_dir, f"{key.replace('.', '_')}.json")
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2)
            
            print(f"Extracted chat data from {key} to {json_file}")
            
            # Extract messages from bubbles structure if present
            if "tabs" in json_data and isinstance(json_data["tabs"], list):
                for tab_idx, tab in enumerate(json_data["tabs"]):
                    if "bubbles" in tab and isinstance(tab["bubbles"], list):
                        # Create a conversation file
                        tab_id = tab.get("tabId", f"tab_{tab_idx}")
                        conversation_file = os.path.join(output_dir, f"conversation_{tab_id}.txt")
                        
                        with open(conversation_file, "w", encoding="utf-8") as f:
                            f.write(f"=== Conversation in {key} / {tab_id} ===\n\n")
                            
                            for bubble in tab["bubbles"]:
                                bubble_type = bubble.get("type", "unknown")
                                content = bubble.get("content", "")
                                
                                f.write(f"[{bubble_type.upper()}]\n")
                                f.write(f"{content}\n\n")
                                
                                # Also check for tool calls
                                if "toolResults" in bubble:
                                    for tool_result in bubble["toolResults"]:
                                        f.write(f"[TOOL CALL] {tool_result.get('name', 'unknown')}\n")
                                        f.write(f"{tool_result.get('result', '')}\n\n")
                        
                        print(f"Extracted conversation to {conversation_file}")
                        extracted_chats.append(conversation_file)
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            # If can't decode as JSON, try as text
            try:
                text_value = value.decode('utf-8', errors='ignore')
                if "chat" in text_value or "bubble" in text_value or "conversation" in text_value:
                    text_file = os.path.join(output_dir, f"{key.replace('.', '_')}.txt")
                    with open(text_file, "w", encoding="utf-8") as f:
                        f.write(text_value)
                    print(f"Extracted text from {key} to {text_file}")
            except (AttributeError, UnicodeDecodeError):
                pass
    
    # Now try to extract from cursorDiskKV
    cursor.execute("SELECT key, value FROM cursorDiskKV WHERE key LIKE '%chat%' OR key LIKE '%bubble%' OR key LIKE '%conversation%'")
    chat_related_rows = cursor.fetchall()
    
    for key, value in chat_related_rows:
        # Skip if value is None
        if value is None:
            print(f"Skipping cursorDiskKV.{key} with None value")
            continue
            
        try:
            # Try to decode as JSON
            json_data = json.loads(value)
            
            # Save as JSON file
            json_file = os.path.join(output_dir, f"cursor_{key.replace('.', '_')}.json")
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2)
            
            print(f"Extracted chat data from cursorDiskKV.{key} to {json_file}")
            
            # Create a conversation file if it has text content
            if "text" in json_data and json_data["text"]:
                text_file = os.path.join(output_dir, f"cursor_{key.replace('.', '_')}.txt")
                with open(text_file, "w", encoding="utf-8") as f:
                    f.write(json_data["text"])
                print(f"Extracted message text to {text_file}")
                extracted_chats.append(text_file)
                
            # If it has toolFormerData with command output
            if "toolFormerData" in json_data and "result" in json_data["toolFormerData"]:
                try:
                    # Skip if result is None
                    if json_data["toolFormerData"]["result"] is None:
                        continue
                        
                    result_data = json.loads(json_data["toolFormerData"]["result"])
                    if "output" in result_data:
                        tool_output_file = os.path.join(output_dir, f"cursor_{key.replace('.', '_')}_tool_output.txt")
                        with open(tool_output_file, "w", encoding="utf-8") as f:
                            f.write(result_data["output"])
                        print(f"Extracted tool output to {tool_output_file}")
                        extracted_chats.append(tool_output_file)
                except (json.JSONDecodeError, TypeError):
                    pass
                
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            # If can't decode as JSON, try as text
            try:
                text_value = value.decode('utf-8', errors='ignore')
                if "chat" in text_value or "bubble" in text_value or "conversation" in text_value or "node demo.js" in text_value:
                    text_file = os.path.join(output_dir, f"cursor_{key.replace('.', '_')}.txt")
                    with open(text_file, "w", encoding="utf-8") as f:
                        f.write(text_value)
                    print(f"Extracted text from cursorDiskKV.{key} to {text_file}")
                    extracted_chats.append(text_file)
            except (AttributeError, UnicodeDecodeError):
                pass
    
    # Create a README file with summary
    with open(os.path.join(output_dir, "README.md"), "w") as f:
        f.write("# Extracted Chat History\n\n")
        f.write(f"Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total files extracted: {len(extracted_chats)}\n\n")
        f.write("## Files\n\n")
        
        for chat_file in extracted_chats:
            basename = os.path.basename(chat_file)
            f.write(f"- [{basename}](./{basename})\n")
    
    conn.close()
    print(f"\nChat extraction complete. All files saved to {output_dir}")
    print(f"Check {os.path.join(output_dir, 'README.md')} for a summary of extracted files")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sqlite_dump.py <path_to_state.vscdb> [action] [output_directory]")
        print("\nActions:")
        print("  dump      - Dump the entire database (default)")
        print("  extract   - Only extract chat history")
        print("  both      - Perform both operations")
        sys.exit(1)
    
    db_path = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) >= 3 else "dump"
    
    if action == "dump" or action == "both":
        output_dir = sys.argv[3] if len(sys.argv) >= 4 else "sqlite_dump"
        dump_sqlite_db(db_path, output_dir)
    
    if action == "extract" or action == "both":
        output_dir = sys.argv[3] if len(sys.argv) >= 4 else "extracted_chats"
        extract_chats(db_path, output_dir) 