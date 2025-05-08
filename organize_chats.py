#!/usr/bin/env python3

import json
import os
import glob
import re
from datetime import datetime
import shutil
import sys

def organize_chats(input_dir="extracted_chats", output_dir="organized_chats"):
    """
    Organize the extracted chat files into coherent conversation threads
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Helper function to clean title text for display
    def clean_title_text(text):
        # Remove code blocks (both ``` and single line `)
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`[^`]*`', '', text)
        # Remove special markdown chars
        text = re.sub(r'[#*_~\[\](){}]', '', text)
        # Clean up whitespace (multiple spaces, newlines, etc)
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing whitespace
        return text.strip()
    
    # Helper function to find all conversation files in the output directory
    def find_conversation_files(directory):
        result = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".md") and "conversation" in file.lower() and file != "index.md":
                    result.append(os.path.join(root, file))
        return result
    
    # Step 1: Find all conversation files (legacy, might not be primary source for new logic)
    conversation_files = glob.glob(os.path.join(input_dir, "conversation_*.txt"))
    
    # Step 2: Find all bubble files (messages - primary source for detailed conversations)
    # These are typically named like cursor_bubbleId:MAIN_CONVERSATION_ID:MESSAGE_ID.json
    bubble_files = glob.glob(os.path.join(input_dir, "cursor_bubbleId:*.json"))
    
    # Step 3: Find all tool output files (can be linked to messages)
    tool_output_files = glob.glob(os.path.join(input_dir, "*_tool_output.txt"))
    
    print(f"Found {len(conversation_files)} legacy conversation files")
    print(f"Found {len(bubble_files)} message bubble JSON files")
    print(f"Found {len(tool_output_files)} tool output files")
    
    # Create an index file
    with open(os.path.join(output_dir, "index.md"), "w", encoding="utf-8") as index_file:
        index_file.write("# Chat History Index\n\n")
        index_file.write(f"Organized on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        conversation_files_processed = False
        
        # Organize bubbles by main conversation ID (bubbleId from filename)
        if bubble_files:
            index_file.write("\n## Message Bubbles (Conversations)\n\n")
            
            bubble_groups = {}
            for bubble_file_path in bubble_files:
                # Filename pattern: cursor_bubbleId:MAIN_ID:MESSAGE_ID.json
                # We want to group by MAIN_ID
                match = re.search(r'cursor_bubbleId:([^:]+):', os.path.basename(bubble_file_path))
                if match:
                    main_bubble_id = match.group(1)
                    if main_bubble_id not in bubble_groups:
                        bubble_groups[main_bubble_id] = []
                    bubble_groups[main_bubble_id].append(bubble_file_path)
            
            # Process each bubble group (conversation thread)
            sorted_bubble_group_keys = sorted(list(bubble_groups.keys())) # Sort for consistent output order

            for i, bubble_id in enumerate(sorted_bubble_group_keys):
                files_in_group = sorted(bubble_groups[bubble_id]) # Sort files within a group (e.g., by message_id part of filename)
                
                bubble_dir_name = f"bubble_{i+1:03d}_{bubble_id}"
                bubble_dir_path = os.path.join(output_dir, bubble_dir_name)
                os.makedirs(bubble_dir_path, exist_ok=True)
                
                messages = []
                
                for file_path in files_in_group:
                    basename = os.path.basename(file_path)
                    # Extract message_id from filename like cursor_bubbleId:MAIN_ID:MESSAGE_ID.json
                    message_id_match = re.search(r'cursor_bubbleId:[^:]+:([^.]+)\.json', basename)
                    message_id = message_id_match.group(1) if message_id_match else "unknown_msg_id"                    
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        
                        text = data.get("text", "")
                        sender = "user" if data.get("type") == 1 else "assistant"
                        attachments = []

                        # For User messages
                        if sender == "user":
                            current_attachment_files = set()
                            # From context.fileSelections
                            if "context" in data and "fileSelections" in data["context"]:
                                for selection in data["context"].get("fileSelections", []):
                                    uri = selection.get("uri", {})
                                    file_path_from_uri = uri.get("fsPath") or uri.get("path")
                                    if file_path_from_uri:
                                        file_basename = os.path.basename(file_path_from_uri)
                                        attachments.append(f"File: {file_basename}")
                                        current_attachment_files.add(file_basename)
                            
                            # From attachedFileCodeChunksUris
                            for chunk_uri_obj in data.get("attachedFileCodeChunksUris", []):
                                file_path_from_chunk = chunk_uri_obj.get("path")
                                if file_path_from_chunk:
                                    file_basename = os.path.basename(file_path_from_chunk)
                                    if file_basename not in current_attachment_files:
                                        attachments.append(f"File: {file_basename}")
                                        current_attachment_files.add(file_basename)

                        # For Assistant messages
                        elif sender == "assistant":
                            # Code Blocks associated with files
                            for code_block in data.get("codeBlocks", []):
                                uri = code_block.get("uri", {})
                                file_path_from_uri = uri.get("path") or uri.get("_fsPath") # Check both 'path' and '_fsPath'
                                if file_path_from_uri:
                                    attachments.append(f"Code Block for: {os.path.basename(file_path_from_uri)}")
                            
                            # Symbol Links
                            for symbol_link_item in data.get("symbolLinks", []):
                                try:
                                    # Handle both string and dict types
                                    if isinstance(symbol_link_item, dict):
                                        symbol_link = symbol_link_item
                                    else:
                                        symbol_link = json.loads(symbol_link_item)
                                    
                                    symbol_name = symbol_link.get("symbolName", "N/A")
                                    relative_path = symbol_link.get("relativeWorkspacePath", "N/A")
                                    attachments.append(f"Symbol Link: {symbol_name} in {relative_path}")
                                except (json.JSONDecodeError, TypeError) as e:
                                    print(f"Warning: Could not parse symbolLink in {file_path}: {symbol_link_item} - {e}")
                        
                        attachments = sorted(list(set(attachments))) # Deduplicate and sort

                        # Look for any tool outputs
                        tool_output = ""
                        # Assuming tool output file might be named based on the message JSON file
                        potential_tool_output_file = file_path.replace(".json", "_tool_output.txt")
                        if os.path.exists(potential_tool_output_file): # Check if specific tool output exists
                            with open(potential_tool_output_file, "r", encoding="utf-8") as tf:
                                tool_output = tf.read()
                        elif "toolFormerData" in data and data["toolFormerData"].get("status") == "completed": # Generic check
                             # Try to get result if it's simple string, or indicate complex result
                            raw_result = data["toolFormerData"].get("result","")
                            if isinstance(raw_result, str):
                                try:
                                    # If result is JSON string, pretty print it
                                    parsed_result = json.loads(raw_result)
                                    tool_output = json.dumps(parsed_result, indent=2)
                                except json.JSONDecodeError:
                                    tool_output = raw_result # It's a plain string
                            elif raw_result: # Not a string, but not empty
                                tool_output = json.dumps(raw_result, indent=2)


                        messages.append({
                            "id": message_id,
                            "sender": sender,
                            "text": text,
                            "attachments": attachments,
                            "tool_output": tool_output,
                            "original_file": basename
                        })                        
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        print(f"Error processing {file_path}: {e}")
                
                # Sort messages by original filename (which includes message_id)
                # This is a common heuristic for ordering if message_ids are sortable
                messages.sort(key=lambda m: m["original_file"])
                
                conversation_md_file = os.path.join(bubble_dir_path, "conversation.md")
                with open(conversation_md_file, "w", encoding="utf-8") as f:
                    f.write(f"# Conversation from Bubble {bubble_id}\n\n")
                    
                    for message in messages:
                        sender_marker = "👤 User:" if message["sender"] == "user" else "🤖 Assistant:"
                        f.write(f"## {sender_marker}\n\n")
                        
                        if message['text'] or not (message["attachments"] or message["tool_output"]):
                            f.write(f"{message['text']}\n\n")
                        elif not message['text'] and (message["attachments"] or message["tool_output"]):
                            # If text is empty but there are attachments or tool output, add a placeholder or just proceed
                            f.write("\n") # Ensures a blank line if text is empty but attachments follow

                        if message["attachments"]:
                            f.write("### Attached:\n")
                            for att in message["attachments"]:
                                f.write(f"- {att}\n")
                            f.write("\n")
                        
                        if message["tool_output"]:
                            f.write("### Tool Output:\n\n")
                            f.write("```\n") # Start code block for tool output
                            f.write(message["tool_output"])
                            f.write("\n```\n\n") # End code block
                
                first_message_text = messages[0]["text"] if messages and messages[0]["text"] else f"Conversation {bubble_id}"
                
                # Clean the title text - remove markdown code blocks and other problematic formatting
                clean_text = clean_title_text(first_message_text)
                
                # If after cleaning we have empty text, use the bubble ID
                if not clean_text:
                    title = f"Conversation {bubble_id}"
                else:
                    # Truncate if still too long
                    title = clean_text[:60] + "..." if len(clean_text) > 60 else clean_text
                
                index_file.write(f"- [{title}](./{bubble_dir_name}/conversation.md) ({len(messages)} messages)\n")
                
                # Copy all related JSON files to the bubble directory
                for file_path_to_copy in files_in_group:
                    shutil.copy2(file_path_to_copy, os.path.join(bubble_dir_path, os.path.basename(file_path_to_copy)))
                    
                    # Copy associated tool output if exists
                    potential_tool_output_file = file_path_to_copy.replace(".json", "_tool_output.txt")
                    if os.path.exists(potential_tool_output_file):
                        shutil.copy2(potential_tool_output_file, os.path.join(bubble_dir_path, os.path.basename(potential_tool_output_file)))

        # Process legacy conversation files (if any, and if desired)
        if conversation_files:
            conversation_files_processed = True
            index_file.write("\n## Legacy Conversations (from .txt files)\n\n")
            for i, conv_file_path in enumerate(conversation_files):
                # This part remains as is, as it processes different source files
                basename = os.path.basename(conv_file_path)
                conv_id = basename.replace("conversation_", "").replace(".txt", "")
                
                with open(conv_file_path, "r", encoding="utf-8") as f_content:
                    content = f_content.read()
                
                first_line = content.split("\n", 2)[0] if "\n" in content else content[:50]
                raw_title = first_line.replace("=== Conversation in ", "").replace(" ===", "")
                
                # Apply the same title cleaning logic
                clean_title = clean_title_text(raw_title)
                if not clean_title:
                    title = f"Legacy Conversation {conv_id}"
                else:
                    title = clean_title[:57] + "..." if len(clean_title) > 57 else clean_title
                
                new_filename = f"legacy_conversation_{i+1:03d}_{conv_id}.md"
                with open(os.path.join(output_dir, new_filename), "w", encoding="utf-8") as f_new:
                    f_new.write(f"# Legacy Conversation: {clean_title}\n\n")
                    f_new.write(f"ID: {conv_id}\n\n")
                    f_new.write("```\n")
                    f_new.write(content)
                    f_new.write("\n```\n")
                
                index_file.write(f"- (Legacy) [{title}](./{new_filename})\n")

        # If no bubble or conversation files were processed, try to find existing conversation files
        if not bubble_files and not conversation_files_processed:
            # Find all conversation.md files in the output directory
            conversation_md_files = find_conversation_files(output_dir)
            if conversation_md_files:
                index_file.write("\n## Existing Conversations\n\n")
                for i, conv_file_path in enumerate(conversation_md_files):
                    # Get the relative path to the output directory
                    rel_path = os.path.relpath(conv_file_path, output_dir)
                    
                    # Read the file to extract a title
                    with open(conv_file_path, "r", encoding="utf-8") as f_content:
                        first_line = f_content.readline().strip()
                        title = first_line.replace("# ", "")
                        if len(title) > 60:
                            title = title[:57] + "..."
                    
                    index_file.write(f"- [{title}](./{rel_path})\n")

        # Section for specific search term (add only if desired)
        search_term = "node demo.js departures 8100013"
        index_file.write(f"\n## Search Results for '{search_term}'\n\n")
        search_results_list = []
        # This search might need to be adapted if tool_output_files are not the sole source
        for tool_file_path in tool_output_files:
            with open(tool_file_path, "r", encoding="utf-8") as f_tool:
                content = f_tool.read()
                if search_term in content:
                    search_results_list.append({
                        "file": tool_file_path,
                        "content": content
                    })
        
        if search_results_list:
            search_result_md_file = os.path.join(output_dir, "search_results_node_demo.md")
            with open(search_result_md_file, "w", encoding="utf-8") as f_search:
                f_search.write(f"# Search Results for '{search_term}'\n\n")
                for idx, result in enumerate(search_results_list):
                    filename = os.path.basename(result["file"])
                    f_search.write(f"## Match {idx+1}: {filename}\n\n")
                    f_search.write("```\n")
                    f_search.write(result["content"])
                    f_search.write("\n```\n\n")
            
            index_file.write(f"Found {len(search_results_list)} matches. [View all 'node demo.js' matches](./search_results_node_demo.md)\n\n")
        else:
            index_file.write(f"No matches found for '{search_term}'.\n")
    
    print(f"\nChat organization complete. All files saved to {output_dir}")
    print(f"Check {os.path.join(output_dir, 'index.md')} for an index of all conversations")

if __name__ == "__main__":
    # Default input_dir can be changed here if needed, e.g. from sys.argv
    input_dir_arg = "extracted_chats" 
    output_dir_arg = "organized_chats"

    if len(sys.argv) > 1:
        input_dir_arg = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir_arg = sys.argv[2]
        
    print(f"Running chat organization from '{input_dir_arg}' to '{output_dir_arg}'")
    organize_chats(input_dir=input_dir_arg, output_dir=output_dir_arg) 