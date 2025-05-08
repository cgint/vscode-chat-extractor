# VSCode Chat History Extractor

This set of tools helps extract chat history data from VSCode's SQLite database file (`state.vscdb`).

## Available Scripts

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

## Output Files

Each script creates a directory with various output files:
- `.json` files containing structured data
- `.txt` files with human-readable content
- `.bin` files with raw binary data when needed

## Requirements

- Python 3.6+
- SQLite3 (usually included with Python)

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