#!/bin/bash

# Extract and organize chat data from VSCode's state.vscdb file
# Usage: ./extract_and_organize.sh <path_to_state.vscdb>

set -e  # Exit on error

# Check if a database file was provided
if [ $# -lt 1 ]; then
    echo "Usage: ./extract_and_organize.sh <path_to_state.vscdb>"
    exit 1
fi

DB_PATH="$1"
BASE_DIR=$(dirname "$0")
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
EXTRACTED_CHATS_DIR="extracted_chats"
DEEP_SEARCH_DIR="found_matches"
ORGANIZED_CHATS_DIR="organized_chats"

# Verify database file exists
if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database file '$DB_PATH' not found!"
    exit 1
fi

echo "==== Starting extraction process ===="
echo "Database: $DB_PATH"
echo "Timestamp: $TIMESTAMP"
echo ""

# Create output directories
mkdir -p "$EXTRACTED_CHATS_DIR" "$DEEP_SEARCH_DIR" "$ORGANIZED_CHATS_DIR"

# Step 1: Extract chat data using deep_search_extract.py
echo "Step 1: Running deep search to extract chat content..."
python "$BASE_DIR/deep_search_extract.py" "$DB_PATH" "chat" "$DEEP_SEARCH_DIR"
echo "Deep search completed, results in: $DEEP_SEARCH_DIR"
echo ""

# Step 2: Extract chat data using extract_chat.py
echo "Step 2: Extracting chat data..."
python "$BASE_DIR/extract_chat.py" "$DB_PATH" "$EXTRACTED_CHATS_DIR"
echo "Chat data extracted to: $EXTRACTED_CHATS_DIR"
echo ""

# Step 3: Organize the extracted chats
echo "Step 3: Organizing chat data..."
python "$BASE_DIR/organize_chats.py" "$EXTRACTED_CHATS_DIR" "$ORGANIZED_CHATS_DIR"
echo "Chat organization complete. Organized chats in: $ORGANIZED_CHATS_DIR"
echo ""

# Create a summary file
SUMMARY_FILE="extraction_summary_${TIMESTAMP}.txt"
echo "Creating summary file: $SUMMARY_FILE"

{
    echo "VSCode Chat Extraction Summary"
    echo "=============================="
    echo "Run on: $(date)"
    echo "Database: $DB_PATH"
    echo ""
    echo "Output Directories:"
    echo "- Deep Search Results: $DEEP_SEARCH_DIR"
    echo "- Extracted Chats: $EXTRACTED_CHATS_DIR"
    echo "- Organized Chats: $ORGANIZED_CHATS_DIR"
    echo ""
    echo "Next Steps:"
    echo "1. Check $ORGANIZED_CHATS_DIR/index.md for an index of all conversations"
    echo "2. Look in $DEEP_SEARCH_DIR for specific search matches"
} > "$SUMMARY_FILE"

echo "==== Extraction process complete ===="
echo "See $SUMMARY_FILE for a summary of all outputs"
echo "Main output for viewing conversations: $ORGANIZED_CHATS_DIR/index.md" 