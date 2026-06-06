#!/bin/bash
#
# This script installs system dependencies required by the Tender Management app.
#
echo "This script will attempt to install 'unoconv' for DOCX to PDF conversion."
echo "You may be prompted for your administrator (sudo) password."

# Check if sudo is available
if ! [ -x "$(command -v sudo)" ]; then
    echo 'Error: sudo is not installed. Please run this script as a user with root privileges.' >&2
    exit 1
fi

sudo apt-get update && sudo apt-get install -y unoconv

echo ""
echo "Dependency 'unoconv' has been installed."
echo "Please run 'bench restart' to ensure all services pick up the new tool."
