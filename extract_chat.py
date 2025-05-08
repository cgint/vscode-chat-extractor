#!/usr/bin/env python3

import sqlite3
import json
import os
import sys
import re

def extract_chat_data(db_path, output_dir="extracted_chats"):
    """
    Extract chat data from the VSCode state database
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all keys related to chat data
    cursor.execute("SELECT key, value FROM ItemTable WHERE key LIKE '%chat%'")
    chat_data = cursor.fetchall()
    
    # Search through all tables for specific content
    search_term = "node demo.js departures 8100013"
    print(f"Searching for: {search_term}")
    
    # Use a regex pattern to find binary data containing the search term
    pattern = re.compile(search_term.encode('utf-8'))
    
    matches = []
    messages = []
    
    for key, value in chat_data:
        try:
            # First try to decode as JSON
            data = json.loads(value)
            json_str = json.dumps(data, indent=2)
            
            if search_term in json_str:
                matches.append((key, json_str))
                output_file = os.path.join(output_dir, f"{key.replace('.', '_')}.json")
                with open(output_file, "w") as f:
                    f.write(json_str)
                print(f"Saved JSON match to {output_file}")
                
                # Try to extract messages from the data structure
                if "tabs" in data:
                    for tab in data["tabs"]:
                        if "bubbles" in tab:
                            for bubble in tab["bubbles"]:
                                if "content" in bubble:
                                    messages.append(bubble["content"])
        except (json.JSONDecodeError, UnicodeDecodeError):
            # If not JSON, check if raw binary data contains the search term
            if pattern.search(value):
                matches.append((key, "Binary data matched"))
                
                # Save raw binary data
                binary_file = os.path.join(output_dir, f"{key.replace('.', '_')}.bin")
                with open(binary_file, "wb") as f:
                    f.write(value)
                print(f"Saved binary match to {binary_file}")
    
    # Also search in all tables for any text matching the search term
    for table in ["ItemTable", "cursorDiskKV"]:
        cursor.execute(f"SELECT key, value FROM {table}")
        rows = cursor.fetchall()
        
        for key, value in rows:
            try:
                # Check if the value contains the search term as a string
                text_value = value.decode('utf-8', errors='ignore')
                if search_term in text_value:
                    matches.append((key, "Text match in " + table))
                    text_file = os.path.join(output_dir, f"{table}_{key.replace('.', '_')}.txt")
                    with open(text_file, "w") as f:
                        f.write(text_value)
                    print(f"Saved text match to {text_file}")
            except:
                # If decoding fails, check binary data
                if isinstance(value, bytes) and pattern.search(value):
                    matches.append((key, "Binary match in " + table))
                    binary_file = os.path.join(output_dir, f"{table}_{key.replace('.', '_')}.bin")
                    with open(binary_file, "wb") as f:
                        f.write(value)
                    print(f"Saved binary match to {binary_file}")
    
    conn.close()
    
    # Print summary of matches
    print("\nMatches found:")
    for key, match_type in matches:
        print(f"- {key}: {match_type}")
    
    return matches

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_chat.py <path_to_state.vscdb> [output_directory]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) >= 3 else "extracted_chats"
    
    extract_chat_data(db_path, output_dir) 