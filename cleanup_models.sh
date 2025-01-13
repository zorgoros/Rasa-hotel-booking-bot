#!/bin/bash

# Directory where Rasa models are stored
MODEL_DIR="models"

# Number of days after which models should be deleted
DAYS_OLD=30

# Find and delete models older than the specified number of days
find "$MODEL_DIR" -type f -name '*.tar.gz' -mtime +$DAYS_OLD -exec rm {} \;

echo "Cleanup complete. Models older than $DAYS_OLD days have been deleted."

: '
This script automates the cleanup of old Rasa models by deleting files older than a specified number of days.

Instructions for Use:
1. **Setup**:
   - Save this script as `cleanup_models.sh` in your desired directory.
   - Ensure the script is executable by running: `chmod +x cleanup_models.sh`.

2. **Manual Execution**:
   - You can run the script manually by executing: `./cleanup_models.sh`.
   - This will delete all `.tar.gz` files in the `models` directory that are older than 30 days.

3. **Automate with Cron**:
   - To automate the script to run monthly, use the cron job scheduler.
   - Open the crontab editor by running: `crontab -e`.
   - Add the following line to schedule the script to run on the first day of every month at midnight:
     ```
     0 0 1 * * /full/path/to/your/cleanup_models.sh
     ```
   - Replace `/full/path/to/your/cleanup_models.sh` with the actual full path to your script.

4. **Verify Cron Job**:
   - After saving the crontab file, verify your cron jobs by running: `crontab -l`.

5. **Logging (Optional)**:
   - To log the output of the script, modify the cron job entry to redirect output to a log file:
     ```
     0 0 1 * * /full/path/to/your/cleanup_models.sh >> /full/path/to/your/cleanup_log.txt 2>&1
     ```

6. **Permissions**:
   - Ensure the user running the cron job has the necessary permissions to execute the script and delete files in the `models` directory.

By following these instructions, you can automate the cleanup of old Rasa models, ensuring your project directory remains organized without manual intervention.
'