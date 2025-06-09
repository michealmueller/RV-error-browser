# Documentation Archiving System

This document describes the automated documentation archiving system used in the project.

## Overview

The documentation archiving system automatically creates compressed archives of the `docs/` directory to optimize context usage and maintain a history of documentation changes.

## Components

1. **Archive Script** (`scripts/archive_docs.sh`)
   - Creates timestamped `.tar.gz` archives
   - Maintains the last 5 archives
   - Stores archives in the `archives/` directory
   - Format: `docs_archive_YYYYMMDD_HHMMSS.tar.gz`

2. **Automation Methods**
   - **Git Hooks** (Primary Method)
     - Pre-commit hook creates archive before each commit
     - Automatically adds new archives to git
     - Ensures documentation is archived with code changes
   
   - **Cron Job** (Alternative Method)
     - Hourly archiving via cron
     - Independent of git operations
     - Good for regular backups

## Usage

### Manual Archiving
```bash
./scripts/archive_docs.sh
```

### Setting Up Automation

1. **Git Hooks** (Already configured)
   - Located in `.git/hooks/pre-commit`
   - Runs automatically on commit
   - No additional setup needed

2. **Cron Job** (Optional)
   ```bash
   ./scripts/setup_cron.sh
   ```

## Archive Management

- Archives are stored in `archives/` directory
- Only the last 5 archives are retained
- Older archives are automatically removed
- Each archive is timestamped for easy reference

## Benefits

1. **Context Optimization**
   - Compressed archives use less context space
   - Single archive reference instead of multiple files
   - Efficient storage of documentation history

2. **Version Control**
   - Documentation changes are tracked with code
   - Easy rollback to previous documentation versions
   - Maintains documentation history

3. **Space Efficiency**
   - Automatic cleanup of old archives
   - Compressed storage format
   - Controlled growth of archive directory

## Maintenance

- Archives are automatically managed by the system
- No manual cleanup required
- Last 5 archives are always available
- Each archive is self-contained and can be extracted independently

## Troubleshooting

If archives are not being created:

1. Check script permissions:
   ```bash
   chmod +x scripts/archive_docs.sh
   ```

2. Verify git hook:
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

3. Check cron job (if enabled):
   ```bash
   crontab -l
   ```

## Best Practices

1. Always commit documentation changes to trigger archiving
2. Use the latest archive for context sharing
3. Keep the `docs/` directory organized
4. Monitor the `archives/` directory size if needed 