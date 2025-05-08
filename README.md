# VSCode Chat History Extractor

This set of tools helps extract chat history data from VSCode's SQLite database file (`state.vscdb`).

## Quick Start (All-in-One Script)

The easiest way to extract, organize, and visualize your chat history is with the `extract_and_organize.sh` script:

```bash
# Extract with clean titles, generate HTML and a single-page HTML file containing all conversations
./extract_and_organize.sh -c -h -s path/to/state.vscdb

# Extract with clean titles and generate HTML files
./extract_and_organize.sh -c -h path/to/state.vscdb

# Extract with original titles only
./extract_and_organize.sh path/to/state.vscdb
```

Options:
- `-c, --clean`: Use sanitized titles (removes markdown formatting and code blocks)
- `-h, --html`: Generate HTML versions of all markdown files (requires `markdown` Python package)
- `-s, --single`: Generate a single HTML page containing all conversations (automatically enables `-h`)

## Available Individual Scripts

### 1. Extract Specific Chat Content

Use `extract_chat.py` to extract chat data that contains a specific search term:

```bash
python extract_chat.py path/to/state.vscdb [output_directory]
```

This will search for "node demo.js departures 8100013" and save any matches.

### 2. Extract All Chat History

Use `extract_all_chats.py` to extract all chat history data:

```bash
python extract_all_chats.py path/to/state.vscdb [output_directory]
```

This will extract all chat history and save it in human-readable format.

### 3. Deep Search for Specific Content

Use `deep_search_extract.py` to deeply search for specific content in all data:

```bash
python deep_search_extract.py path/to/state.vscdb "your search term" [output_directory]
```

This performs a more thorough search through all binary data and handles multiple encoding formats.

### 4. Organize Extracted Chats

Use `organize_chats.py` to organize the extracted chat data into a more browsable format:

```bash
python organize_chats.py extracted_chats organized_chats
```

This creates an index file and organizes conversations into directories.

### 5. Convert Markdown to HTML

Use `md_to_html.py` to convert all markdown files to HTML for easier viewing in browsers:

```bash
python md_to_html.py organized_chats [output_directory]
```

If no output directory is specified, HTML files will be created alongside markdown files.

## Output Files

Each script creates a directory with various output files:
- `.json` files containing structured data
- `.txt` files with human-readable content
- `.bin` files with raw binary data when needed

## Requirements

- Python 3.6+
- SQLite3 (usually included with Python)
- markdown>=3.4.0 (only needed for HTML generation)

To install required packages:
```bash
pip install -r requirements.txt
```

## Tips for Finding Chat History

1. Chat history in VSCode is typically stored in structured JSON format
2. The main chat data is often found in `workbench.panel.aichat.view.aichat.chatdata`
3. Individual chat sessions may be spread across multiple entries
4. Some data may be stored as binary BLOBs that need special processing
5. The deep search tool can find content even when it's embedded in binary data

## Example Usage

To extract all your chat history:
```bash
python extract_all_chats.py state.vscdb
```

To find a specific conversation containing a code snippet:
```bash
python deep_search_extract.py state.vscdb "node demo.js departures 8100013"
``` 