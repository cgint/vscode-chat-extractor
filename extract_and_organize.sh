#!/bin/bash

# Extract and organize chat data from VSCode's state.vscdb file
# Usage: ./extract_and_organize.sh [options] <path_to_state.vscdb>
#
# Options:
#   -c, --clean     Use cleaned (sanitized) titles in the output index
#   -h, --html      Generate HTML versions of all markdown files
#   -s, --single    Generate a single HTML page containing all conversations

set -e  # Exit on error

# Process command line arguments
CLEAN_TITLES=0
GENERATE_HTML=0
GENERATE_SINGLE_PAGE=0
POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    -c|--clean)
      CLEAN_TITLES=1
      shift # past argument
      ;;
    -h|--html)
      GENERATE_HTML=1
      shift # past argument
      ;;
    -s|--single)
      GENERATE_SINGLE_PAGE=1
      GENERATE_HTML=1  # Single page requires HTML generation
      shift # past argument
      ;;
    -*|--*) 
      echo "Unknown option $1"
      echo "Usage: ./extract_and_organize.sh [-c|--clean] [-h|--html] [-s|--single] <path_to_state.vscdb>"
      exit 1
      ;;
    *) 
      POSITIONAL_ARGS+=("$1") # save positional argument
      shift # past argument
      ;;
  esac
done

# Check if we have a database path
if [ ${#POSITIONAL_ARGS[@]} -eq 0 ]; then
  echo "Error: No database path specified."
  echo "Usage: ./extract_and_organize.sh [-c|--clean] [-h|--html] [-s|--single] <path_to_state.vscdb>"
  exit 1
fi

# Set the database path
DB_PATH="${POSITIONAL_ARGS[0]}"

# Configure options
if [ $CLEAN_TITLES -eq 1 ]; then
  echo "Using clean titles mode (sanitized markdown)"
fi

if [ $GENERATE_HTML -eq 1 ]; then
  echo "HTML generation is enabled"
fi

if [ $GENERATE_SINGLE_PAGE -eq 1 ]; then
  echo "Single-page HTML generation is enabled"
fi

# Create a timestamp for this extraction
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Output directories
MD_OUTPUT_DIR="organized_chats"
HTML_OUTPUT_DIR="organized_chats/html"

# Start the extraction process
echo "==== Starting extraction process ===="
echo "Database: $DB_PATH"
echo "Timestamp: $TIMESTAMP"

# Step 1: Search for chat data using deep search
echo -e "\nStep 1: Running deep search to extract chat content..."
python deep_search_extract.py "$DB_PATH" "chat"
echo "Deep search completed, results in: found_matches"

# Step 2: Extract chat data
echo -e "\nStep 2: Extracting chat data..."
python extract_all_chats.py "$DB_PATH" | grep -v "DEBUG:" | grep -v "INFO:"
echo "Chat data extracted to: extracted_chats"

# Step 3: Organize chat data into markdown files
echo -e "\nStep 3: Organizing chat data..."
echo "Running chat organization from 'extracted_chats' to '$MD_OUTPUT_DIR'"

if [ $CLEAN_TITLES -eq 1 ]; then
  python organize_chats.py --clean extracted_chats "$MD_OUTPUT_DIR"
else
  python organize_chats.py extracted_chats "$MD_OUTPUT_DIR"
fi

if [ $CLEAN_TITLES -eq 1 ]; then
  echo "Chat organization complete with clean titles. Organized chats in: $MD_OUTPUT_DIR"
else
  echo "Chat organization complete. Organized chats in: $MD_OUTPUT_DIR"
fi

# Step 4: Convert markdown files to HTML if requested
if [ $GENERATE_HTML -eq 1 ]; then
  echo -e "\nStep 4: Converting markdown files to HTML..."
  
  # Make sure HTML directory exists
  mkdir -p "$HTML_OUTPUT_DIR"
  
  python md_to_html.py "$MD_OUTPUT_DIR" "$HTML_OUTPUT_DIR"
  echo "HTML conversion complete. HTML files in: $HTML_OUTPUT_DIR"
  
  # Generate single page HTML if requested
  if [ $GENERATE_SINGLE_PAGE -eq 1 ]; then
    echo -e "\nStep 5: Generating single-page HTML..."
    python -c "import md_to_html; md_to_html.generate_single_page('$HTML_OUTPUT_DIR', 'index_one_page.html')"
    echo "Single-page HTML created. File in: $HTML_OUTPUT_DIR/index_one_page.html"
  fi
fi

# Create a summary file
SUMMARY_FILE="extraction_summary_${TIMESTAMP}.txt"
echo "Creating summary file: $SUMMARY_FILE"
{
  echo "VSCode Chat Extraction Summary"
  echo "=============================="
  echo "Timestamp: $TIMESTAMP"
  echo "Database: $DB_PATH"
  echo ""
  echo "Options:"
  echo "- Clean titles: $([ $CLEAN_TITLES -eq 1 ] && echo "YES" || echo "NO")"
  echo "- HTML generation: $([ $GENERATE_HTML -eq 1 ] && echo "YES" || echo "NO")"
  echo "- Single-page HTML: $([ $GENERATE_SINGLE_PAGE -eq 1 ] && echo "YES" || echo "NO")"
  echo ""
  echo "Outputs:"
  echo "- Markdown files: $MD_OUTPUT_DIR/index.md"
  if [ $GENERATE_HTML -eq 1 ]; then
    echo "- HTML files: $HTML_OUTPUT_DIR/index.html"
    if [ $GENERATE_SINGLE_PAGE -eq 1 ]; then
      echo "- Single-page HTML: $HTML_OUTPUT_DIR/index_one_page.html"
    fi
  fi
} > "$SUMMARY_FILE"

echo "==== Extraction process complete ===="
echo "See ${SUMMARY_FILE} for a summary of all outputs"
echo "Main output for viewing conversations:"
echo "- Markdown: $MD_OUTPUT_DIR/index.md"
if [ $GENERATE_HTML -eq 1 ]; then
  echo "- HTML: $HTML_OUTPUT_DIR/index.html"
  if [ $GENERATE_SINGLE_PAGE -eq 1 ]; then
    echo "- Single HTML page: $HTML_OUTPUT_DIR/index_one_page.html"
  fi
fi 