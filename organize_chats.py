#!/usr/bin/env python3

import json
import os
import glob
import re
from datetime import datetime
import shutil

def organize_chats(input_dir="extracted_chats", output_dir="organized_chats"):
    """
    Organize the extracted chat files into coherent conversation threads
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Step 1: Find all conversation files
    conversation_files = glob.glob(os.path.join(input_dir, "conversation_*.txt"))
    
    # Step 2: Find all bubble files (messages)
    bubble_files = glob.glob(os.path.join(input_dir, "cursor_bubbleId:*.json"))
    
    # Step 3: Find all tool output files
    tool_output_files = glob.glob(os.path.join(input_dir, "*_tool_output.txt"))
    
    print(f"Found {len(conversation_files)} conversation files")
    print(f"Found {len(bubble_files)} message bubbles")
    print(f"Found {len(tool_output_files)} tool output files")
    
    # Create an index file
    with open(os.path.join(output_dir, "index.md"), "w") as index_file:
        index_file.write("# Chat History Index\n\n")
        index_file.write(f"Organized on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # First, process and organize conversations
        if conversation_files:
            index_file.write("## Complete Conversations\n\n")
            
            for i, conv_file in enumerate(conversation_files):
                basename = os.path.basename(conv_file)
                conv_id = basename.replace("conversation_", "").replace(".txt", "")
                
                # Read the conversation
                with open(conv_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Try to extract a title or first few words
                first_line = content.split("\n", 2)[0] if "\n" in content else content[:50]
                title = first_line.replace("=== Conversation in ", "").replace(" ===", "")
                if len(title) > 60:
                    title = title[:57] + "..."
                
                # Create a new file with the conversation
                new_filename = f"conversation_{i+1:03d}_{conv_id}.md"
                with open(os.path.join(output_dir, new_filename), "w", encoding="utf-8") as f:
                    f.write(f"# Conversation: {title}\n\n")
                    f.write(f"ID: {conv_id}\n\n")
                    f.write("```\n")
                    f.write(content)
                    f.write("\n```\n")
                
                # Add to index
                index_file.write(f"- [{title}](./{new_filename})\n")
        
        # Next, organize bubbles by bubble ID
        if bubble_files:
            index_file.write("\n## Message Bubbles\n\n")
            
            # Group files by bubble ID
            bubble_groups = {}
            for bubble_file in bubble_files:
                match = re.search(r'bubbleId:([^:]+)', bubble_file)
                if match:
                    bubble_id = match.group(1)
                    if bubble_id not in bubble_groups:
                        bubble_groups[bubble_id] = []
                    bubble_groups[bubble_id].append(bubble_file)
            
            # Process each bubble group
            for i, (bubble_id, files) in enumerate(bubble_groups.items()):
                # Create a directory for this bubble group
                bubble_dir = os.path.join(output_dir, f"bubble_{i+1:03d}_{bubble_id}")
                os.makedirs(bubble_dir, exist_ok=True)
                
                # Process each file in this group
                messages = []
                
                for file_path in files:
                    basename = os.path.basename(file_path)
                    
                    # Get message ID from filename
                    message_id = basename.split(":")[-1].split(".")[0]
                    
                    # Read and parse JSON
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        
                        # Try to extract text content
                        text = data.get("text", "")
                        
                        # Get sender type (user or assistant)
                        sender = "user" if data.get("type") == 1 else "assistant"
                        
                        # Look for any tool outputs
                        tool_output = ""
                        tool_output_file = file_path.replace(".json", "_tool_output.txt")
                        if os.path.exists(tool_output_file):
                            with open(tool_output_file, "r", encoding="utf-8") as f:
                                tool_output = f.read()
                        
                        messages.append({
                            "id": message_id,
                            "sender": sender,
                            "text": text,
                            "tool_output": tool_output
                        })
                        
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        print(f"Error processing {file_path}: {e}")
                
                # Sort messages (might not be perfect)
                # Assumes messages were extracted in order
                
                # Create a markdown file with the conversation
                conversation_file = os.path.join(bubble_dir, "conversation.md")
                with open(conversation_file, "w", encoding="utf-8") as f:
                    f.write(f"# Conversation from Bubble {bubble_id}\n\n")
                    
                    for message in messages:
                        sender_marker = "👤 User:" if message["sender"] == "user" else "🤖 Assistant:"
                        f.write(f"## {sender_marker}\n\n")
                        f.write(f"{message['text']}\n\n")
                        
                        if message["tool_output"]:
                            f.write("### Tool Output:\n\n")
                            f.write("```\n")
                            f.write(message["tool_output"])
                            f.write("\n```\n\n")
                
                # Add to index
                first_message = messages[0]["text"] if messages else ""
                title = first_message[:60] + "..." if len(first_message) > 60 else first_message
                
                # Format title with search term indicator
                index_file.write(f"- [Bubble {i+1}: {title}](./bubble_{i+1:03d}_{bubble_id}/conversation.md) ({len(messages)} messages)\n")
                
                # Copy all related files to the bubble directory
                for file_path in files:
                    basename = os.path.basename(file_path)
                    shutil.copy2(file_path, os.path.join(bubble_dir, basename))
                    
                    # Copy associated tool output if exists
                    tool_output_file = file_path.replace(".json", "_tool_output.txt")
                    if os.path.exists(tool_output_file):
                        shutil.copy2(tool_output_file, os.path.join(bubble_dir, os.path.basename(tool_output_file)))
        
        # Add a section specifically for "node demo.js departures 8100013" search results
        index_file.write("\n## Search Results for 'node demo.js departures 8100013'\n\n")
        
        search_results = []
        for tool_file in tool_output_files:
            with open(tool_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "node demo.js departures 8100013" in content:
                    search_results.append({
                        "file": tool_file,
                        "content": content
                    })
        
        if search_results:
            # Create a separate file with all search matches
            search_result_file = os.path.join(output_dir, "search_results.md")
            with open(search_result_file, "w", encoding="utf-8") as f:
                f.write("# Search Results for 'node demo.js departures 8100013'\n\n")
                
                for i, result in enumerate(search_results):
                    filename = os.path.basename(result["file"])
                    f.write(f"## Match {i+1}: {filename}\n\n")
                    f.write("```\n")
                    f.write(result["content"])
                    f.write("\n```\n\n")
            
            index_file.write(f"Found {len(search_results)} matches. [View all matches](./search_results.md)\n\n")
            
            for i, result in enumerate(search_results):
                filename = os.path.basename(result["file"])
                index_file.write(f"{i+1}. {filename}\n")
        else:
            index_file.write("No matches found.\n")
    
    print(f"\nChat organization complete. All files saved to {output_dir}")
    print(f"Check {os.path.join(output_dir, 'index.md')} for an index of all conversations")

if __name__ == "__main__":
    organize_chats() 