#!/usr/bin/env python3

import os
import sys
import re
from datetime import datetime
import markdown
import shutil

def convert_md_to_html(input_dir="organized_chats", output_dir=None):
    """
    Convert all markdown files in the input directory to HTML
    If output_dir is not specified, HTML files are created alongside the markdown files
    """
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist!")
        sys.exit(1)
    
    # If output_dir is specified, create it and copy all files
    if output_dir:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Copy all files and directories from input_dir to output_dir
        for item in os.listdir(input_dir):
            source = os.path.join(input_dir, item)
            dest = os.path.join(output_dir, item)
            if os.path.isdir(source):
                shutil.copytree(source, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(source, dest)
    else:
        # If no output directory is specified, use the input directory
        output_dir = input_dir

    # Configure Markdown with extensions
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'codehilite'])
    
    # Basic CSS for HTML pages
    css = """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }
        pre, code {
            background-color: #f5f5f5;
            border-radius: 3px;
            padding: 0.2em 0.4em;
            font-family: monospace;
        }
        pre {
            padding: 16px;
            overflow: auto;
        }
        pre code {
            background-color: transparent;
            padding: 0;
        }
        h1, h2, h3, h4 {
            margin-top: 24px;
            margin-bottom: 16px;
        }
        h1 {
            font-size: 2em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }
        h2 {
            font-size: 1.5em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }
        a {
            color: #0366d6;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        blockquote {
            padding: 0 1em;
            color: #6a737d;
            border-left: 0.25em solid #dfe2e5;
            margin: 0;
        }
        table {
            border-collapse: collapse;
            width: 100%;
        }
        table, th, td {
            border: 1px solid #dfe2e5;
        }
        th, td {
            padding: 6px 13px;
        }
        tr:nth-child(even) {
            background-color: #f6f8fa;
        }
    </style>
    """
    
    # Find all markdown files
    md_files = []
    for root, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    
    print(f"Found {len(md_files)} markdown files to convert")
    
    # Create a mapping for all .md to .html paths for link conversion
    md_to_html_paths = {}
    for md_file in md_files:
        # Calculate the relative path from output_dir to the file
        rel_path = os.path.relpath(md_file, output_dir)
        html_path = os.path.splitext(rel_path)[0] + '.html'
        md_to_html_paths[rel_path] = html_path
        
        # Special handling for links to index.md in the root directory
        if rel_path == "index.md":
            md_to_html_paths["index.md"] = "index.html"
    
    # Process index.md first to make sure it's available
    index_md_path = os.path.join(output_dir, "index.md")
    if os.path.exists(index_md_path):
        print(f"Processing index file: {index_md_path}")
        with open(index_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix internal links from .md to .html
        def replace_link(match):
            link = match.group(2)
            # Skip external links (http/https)
            if link.startswith('http://') or link.startswith('https://'):
                return match.group(0)
            
            # Extract the path from the link
            link_path = link
            
            # Initialize base_dir
            base_dir = ""
            
            # If it's a relative path, normalize it based on the current file's location
            if not link.startswith('/'):
                base_dir = os.path.dirname("index.md")  # For index.md base_dir is empty
                link_path = os.path.normpath(os.path.join(base_dir, link))
            
            # Convert to html path if it exists in our mapping
            if link_path in md_to_html_paths:
                # Adjust the link to be relative to the HTML file's location
                new_link = md_to_html_paths[link_path]
                if base_dir:
                    # Calculate relative path from the HTML file to the target HTML file
                    rel_to_base = os.path.relpath(new_link, base_dir)
                    return f'[{match.group(1)}]({rel_to_base})'
                else:
                    return f'[{match.group(1)}]({new_link})'
            
            return match.group(0)
        
        # Apply link replacements
        content = re.sub(r'\[([^\]]+)\]\(([^)]+\.md)(?:\s+"[^"]*")?\)', replace_link, content)
        
        # Convert markdown to HTML
        html_content = md.convert(content)
        
        # Create complete HTML document for index
        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat History Index</title>
    {css}
</head>
<body>
    {html_content}
    <footer>
        <p><small>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
    </footer>
</body>
</html>
"""
        
        # Write HTML to file
        index_html_path = os.path.join(output_dir, "index.html")
        with open(index_html_path, 'w', encoding='utf-8') as f:
            f.write(html_doc)
        
        print("Created index.html from index.md")
    
    # Process each markdown file (except index.md which was already processed)
    for md_file in md_files:
        rel_path = os.path.relpath(md_file, output_dir)
        html_file = os.path.join(output_dir, os.path.splitext(rel_path)[0] + '.html')
        
        # Skip index.md since we already processed it
        if os.path.basename(md_file) == "index.md" and os.path.dirname(rel_path) == "":
            continue
        
        # Ensure directory exists
        html_dir = os.path.dirname(html_file)
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix internal links from .md to .html
        # Match Markdown links like [text](link.md) or [text](./dir/link.md)
        def replace_link(match):
            link = match.group(2)
            # Skip external links (http/https)
            if link.startswith('http://') or link.startswith('https://'):
                return match.group(0)
            
            # Extract the path from the link
            link_path = link
            
            # Initialize base_dir
            base_dir = ""
            
            # If it's a relative path, normalize it based on the current file's location
            if not link.startswith('/'):
                base_dir = os.path.dirname(rel_path)
                link_path = os.path.normpath(os.path.join(base_dir, link))
            
            # Convert to html path if it exists in our mapping
            if link_path in md_to_html_paths:
                # Adjust the link to be relative to the HTML file's location
                new_link = md_to_html_paths[link_path]
                if base_dir:
                    # Calculate relative path from the HTML file to the target HTML file
                    rel_to_base = os.path.relpath(new_link, base_dir)
                    return f'[{match.group(1)}]({rel_to_base})'
                else:
                    return f'[{match.group(1)}]({new_link})'
            
            return match.group(0)
        
        # Apply link replacements
        content = re.sub(r'\[([^\]]+)\]\(([^)]+\.md)(?:\s+"[^"]*")?\)', replace_link, content)
        
        # Convert markdown to HTML
        html_content = md.convert(content)
        
        # Create complete HTML document
        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{os.path.basename(os.path.splitext(md_file)[0])}</title>
    {css}
</head>
<body>
    {html_content}
    <footer>
        <p><small>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
    </footer>
</body>
</html>
"""
        
        # Write HTML to file
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_doc)
        
        print(f"Converted {md_file} to {html_file}")
    
    print(f"\nHTML conversion complete. {len(md_files)} files converted.")

def generate_single_page(input_dir="organized_chats_html", output_file="index_one_page.html"):
    """
    Generate a single HTML page that includes all conversations
    """
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist!")
        return False
    
    # Read the index file to get the structure
    index_path = os.path.join(input_dir, "index.html")
    if not os.path.exists(index_path):
        print(f"Error: Index file '{index_path}' does not exist!")
        return False
    
    with open(index_path, 'r', encoding='utf-8') as f:
        index_content = f.read()
    
    # Extract the header part (including CSS)
    header_match = re.search(r'(<!DOCTYPE.*?<body>)', index_content, re.DOTALL)
    if not header_match:
        print("Error: Could not extract header from index.html")
        return False
    
    header = header_match.group(1)
    
    # Prepare the combined content
    combined_content = [header]
    
    # Add the index content
    body_content_match = re.search(r'<body>(.*?)</body>', index_content, re.DOTALL)
    if body_content_match:
        combined_content.append(body_content_match.group(1))
    else:
        print("Warning: Could not extract body content from index.html")
        combined_content.append("<h1>Chat History - Combined Page</h1>")
    
    combined_content.append("<h2>All Conversations</h2>")
    combined_content.append("<div class='all-conversations'>")
    
    # Find all conversation HTML files in the bubble directories
    conversation_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.html') and file == 'conversation.html':
                conversation_files.append(os.path.join(root, file))
    
    # Sort the conversation files to maintain order
    conversation_files.sort()
    
    # Add each conversation content
    for i, conversation_path in enumerate(conversation_files):
        rel_path = os.path.relpath(conversation_path, input_dir)
        bubble_dir = os.path.dirname(rel_path)
        
        print(f"Adding conversation {i+1}/{len(conversation_files)}: {rel_path}")
        
        try:
            with open(conversation_path, 'r', encoding='utf-8') as f:
                conv_content = f.read()
            
            # Extract just the conversation content (between <body> and </body>)
            conv_match = re.search(r'<body>(.*?)</body>', conv_content, re.DOTALL)
            if conv_match:
                # Add a divider and the conversation content
                combined_content.append(f'<hr id="{bubble_dir}">')
                combined_content.append(f'<h3>Conversation: {bubble_dir}</h3>')
                combined_content.append('<div class="conversation">')
                combined_content.append(conv_match.group(1))
                combined_content.append('</div>')
        except Exception as e:
            print(f"Error processing conversation {rel_path}: {str(e)}")
    
    combined_content.append("</div>")
    
    # Close the HTML
    combined_content.append('</body>\n</html>')
    
    # Write the combined file
    output_path = os.path.join(input_dir, output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(combined_content))
    
    print(f"Single-page HTML created: {output_path}")
    return True

if __name__ == "__main__":
    input_dir = "organized_chats"
    output_dir = None
    
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    print(f"Converting markdown to HTML from {input_dir}" + (f" to {output_dir}" if output_dir else ""))
    convert_md_to_html(input_dir, output_dir)
    
    # Optional: Generate a single page for all conversations
    # generate_single_page(output_dir if output_dir else input_dir) 