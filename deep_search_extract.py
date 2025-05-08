#!/usr/bin/env python3

import sqlite3
import json
import os
import sys
import re

def deep_search_and_extract(db_path, search_term, output_dir="found_matches"):
    """
    Deeply search through all data in the database for a specific search term,
    including binary BLOB data that might contain JSON or text with the term.
    
    This handles VSCode's storage format which may include complex nested structures.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Searching for: '{search_term}'")
    
    # Compile regex patterns for binary and text search
    binary_pattern = re.compile(search_term.encode('utf-8'))
    text_pattern = re.compile(search_term)
    
    # Store all matches
    matches = []
    extracted_content = []
    
    # Search both tables in the database
    for table in ["ItemTable", "cursorDiskKV"]:
        print(f"\nSearching table: {table}")
        cursor.execute(f"SELECT key, value FROM {table}")
        rows = cursor.fetchall()
        
        for key, value in rows:
            # Check if value is a binary BLOB containing our search term
            if isinstance(value, bytes) and binary_pattern.search(value):
                match_info = {
                    "table": table,
                    "key": key,
                    "match_type": "binary"
                }
                
                # Try different decoding methods to extract content
                
                # 1. Try direct UTF-8 decoding
                try:
                    text_value = value.decode('utf-8', errors='ignore')
                    # Find the position of the search term
                    pos = text_value.find(search_term)
                    if pos >= 0:
                        # Extract a window of text around the match
                        start = max(0, pos - 200)
                        end = min(len(text_value), pos + len(search_term) + 200)
                        context = text_value[start:end]
                        
                        match_info["context"] = context
                        match_info["position"] = pos
                        
                        # Save the full text content
                        full_text_file = os.path.join(output_dir, f"{table}_{key.replace('.', '_')}_full.txt")
                        with open(full_text_file, "w", encoding="utf-8") as f:
                            f.write(text_value)
                        
                        print(f"Found match in {key} as text, saved to {full_text_file}")
                        
                        # Also save just the context
                        context_file = os.path.join(output_dir, f"{table}_{key.replace('.', '_')}_context.txt")
                        with open(context_file, "w", encoding="utf-8") as f:
                            f.write(f"Match found at position {pos}:\n")
                            f.write(f"...\n{context}\n...")
                        
                        extracted_content.append({
                            "key": key,
                            "context": context,
                            "full_file": full_text_file,
                            "context_file": context_file
                        })
                except UnicodeDecodeError:
                    pass
                
                # 2. Try JSON decoding (if it's stored as JSON)
                try:
                    json_data = json.loads(value)
                    json_str = json.dumps(json_data, indent=2)
                    
                    if search_term in json_str:
                        match_info["match_type"] = "json"
                        
                        # Save the JSON data
                        json_file = os.path.join(output_dir, f"{table}_{key.replace('.', '_')}.json")
                        with open(json_file, "w", encoding="utf-8") as f:
                            f.write(json_str)
                        
                        print(f"Found match in {key} as JSON, saved to {json_file}")
                        
                        # If it's a chat data structure, try to extract the specific messages
                        if "tabs" in json_data and isinstance(json_data["tabs"], list):
                            for tab in json_data["tabs"]:
                                if "bubbles" in tab and isinstance(tab["bubbles"], list):
                                    for bubble in tab["bubbles"]:
                                        if "content" in bubble and search_term in bubble.get("content", ""):
                                            bubble_content = {
                                                "type": bubble.get("type", "unknown"),
                                                "id": bubble.get("id", ""),
                                                "content": bubble.get("content", "")
                                            }
                                            extracted_content.append(bubble_content)
                except (json.JSONDecodeError, TypeError):
                    pass
                
                # 3. Try to extract text strings from binary data
                try:
                    # Find all strings in the binary data
                    strings = re.findall(b'[\\x20-\\x7E]{8,}', value)
                    for s in strings:
                        str_value = s.decode('utf-8', errors='ignore')
                        if search_term in str_value:
                            match_info["binary_string_match"] = str_value
                            extracted_content.append({
                                "key": key,
                                "binary_string": str_value
                            })
                except:
                    pass
                
                # Save the raw binary data (might be useful for further analysis)
                binary_file = os.path.join(output_dir, f"{table}_{key.replace('.', '_')}.bin")
                with open(binary_file, "wb") as f:
                    f.write(value)
                
                match_info["binary_file"] = binary_file
                matches.append(match_info)
    
    # Save the match information
    with open(os.path.join(output_dir, "match_summary.json"), "w") as f:
        json.dump(matches, f, indent=2)
    
    # Save the extracted content
    with open(os.path.join(output_dir, "extracted_content.json"), "w") as f:
        json.dump(extracted_content, f, indent=2)
    
    # Also save as plain text
    with open(os.path.join(output_dir, "extracted_content.txt"), "w") as f:
        for item in extracted_content:
            if "context" in item:
                f.write(f"=== Extract from {item['key']} ===\n")
                f.write(f"{item['context']}\n\n")
            elif "content" in item:
                f.write(f"=== {item.get('type', 'UNKNOWN').upper()} ===\n")
                f.write(f"{item['content']}\n\n")
            elif "binary_string" in item:
                f.write(f"=== Binary string from {item['key']} ===\n")
                f.write(f"{item['binary_string']}\n\n")
    
    conn.close()
    
    print(f"\nFound {len(matches)} matches.")
    print(f"Extracted {len(extracted_content)} content items.")
    print(f"All results saved to {output_dir}")
    print(f"See {os.path.join(output_dir, 'extracted_content.txt')} for readable output.")
    
    return matches, extracted_content

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python deep_search_extract.py <path_to_state.vscdb> <search_term> [output_directory]")
        sys.exit(1)
    
    db_path = sys.argv[1]
    search_term = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) >= 4 else "found_matches"
    
    deep_search_and_extract(db_path, search_term, output_dir) 