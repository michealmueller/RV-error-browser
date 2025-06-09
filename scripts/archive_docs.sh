#!/bin/bash

# Create timestamp for unique archive name
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="docs_archive_${TIMESTAMP}.tar.gz"

# Create archive of docs directory
tar -czf "${ARCHIVE_NAME}" docs/

# Move archive to a dedicated directory
mkdir -p archives
mv "${ARCHIVE_NAME}" archives/

# Keep only the last 5 archives
ls -t archives/docs_archive_*.tar.gz | tail -n +6 | xargs -r rm

echo "Created archive: archives/${ARCHIVE_NAME}" 