#!/bin/bash

# Get the absolute path of the script
SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/archive_docs.sh"

# Create a cron job to run every hour
(crontab -l 2>/dev/null; echo "0 * * * * ${SCRIPT_PATH}") | crontab -

echo "Cron job set up to run archive_docs.sh every hour" 