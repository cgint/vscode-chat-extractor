#!/bin/bash
echo
echo "This script will search for the string 'now we are like friends' in the extracted content of the vscode database."
echo "When found in the state.vscdb file, we expect to find it in the organized_chats directory."
echo "If not we have a problem."
echo
echo

echo "--------------------------------"
echo
echo "Searching in file state.vscdb... (expected to be found)"
grep -l "now we are like friends" state.vscdb
echo 
echo "--------------------------------"

echo
echo "--------------------------------"
echo "Extracting content from state.vscdb..."
rm -rf organized_chats/
./extract_and_organize.sh state.vscdb
echo
echo "--------------------------------"

echo
echo "--------------------------------"
echo "Searching in dir organized_chats ... (expected to be found as well)"
grep -lr "now we are like friends" organized_chats/
echo
echo "--------------------------------"
echo