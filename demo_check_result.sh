#!/bin/bash

# 1. Set the search keyword
if [ -z "$1" ]; then
    SEARCH_KEY="ARRD4_MOUSE"
else
    SEARCH_KEY=$1
fi

echo "🔍 Searching for data containing '$SEARCH_KEY' on all Workers..."

# 2. Run Ansible and capture the output
# We use 2>/dev/null to discard Ansible error messages, keeping only standard output
OUTPUT=$(ansible -i inventory.ini workers -m shell \
    -a "cat /home/almalinux/*${SEARCH_KEY}*parse.out" \
    2>/dev/null)

# 3. Filter output
# Remove Ansible system messages, keeping only the actual CSV content
CLEAN_DATA=$(echo "$OUTPUT" | grep -v "FAILED" | grep -v "rc=" | grep -v "SUCCESS" | grep -v "CHANGED" | grep -v ">>" | grep -v "No such file")

echo "---------------------------------------------------"

# 4. Check results
if [ -n "$CLEAN_DATA" ]; then
    # Data found -> Print output
    echo "$CLEAN_DATA"
    echo "---------------------------------------------------"
    echo "🎉 DEMO SUCCESS! (CSV results generated)"
else
    # No data found -> Prompt to wait
    echo "⏳ No results found yet."
    echo "   (Possible reason: Workers are still processing. Please wait 30 seconds and try again.)"
fi