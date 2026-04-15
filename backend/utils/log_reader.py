"""
Utility module for reading and sanitizing crawler logs
"""

import os
import re
from datetime import datetime


def sanitize_log_line(line):
    """
    Sanitize log line to hide sensitive information:
    - URL parameters like auth-ln-key=xxx, token=xxx
    - Session IDs, cookies
    - Any key-value pairs that look like credentials
    """
    # Hide URL query parameters (auth-ln-key=xxx, token=xxx, etc.)
    # Pattern: key=value in URLs (alphanumeric key, alphanumeric/._- value)
    line = re.sub(r'(\?[a-zA-Z0-9_-]+=)[^\&\s]*', r'\1****', line)
    line = re.sub(r'(\&[a-zA-Z0-9_-]+=)[^\&\s]*', r'\1****', line)

    # Hide JSON-like key-value pairs that look like tokens/session data
    line = re.sub(r'"(token|sessionid|session|cookie|auth)"\s*:\s*"[^"]*"', r'"\1": "****"', line, flags=re.IGNORECASE)
    line = re.sub(r"'(token|sessionid|session|cookie|auth)'\s*:\s*'[^']*'", r"'\1': '****'", line, flags=re.IGNORECASE)

    return line


def read_fetch_log(log_file_path):
    """
    Read fetch log file and return sanitized content.

    Args:
        log_file_path: Path to the crawler log file

    Returns:
        dict: {
            "running": bool,
            "startTime": str (ISO format) or None,
            "logs": list of sanitized log lines
        }
    """
    # Check if log file exists
    if not os.path.exists(log_file_path):
        return {
            "running": False,
            "startTime": None,
            "logs": []
        }

    # Get file modification time as startTime
    stat = os.stat(log_file_path)
    start_time = datetime.fromtimestamp(stat.st_mtime).isoformat()

    # Check if crawler is running by checking file age
    # If file was modified within last 2 minutes, consider it running
    file_age_seconds = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds()
    is_running = file_age_seconds < 120  # 2 minutes threshold

    # Only return logs if crawler is running
    # When not running, return empty logs (old logs are not relevant)
    logs = []
    if is_running:
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Get last 100 lines
                lines = lines[-100:] if len(lines) > 100 else lines
                # Sanitize each line
                logs = [sanitize_log_line(line.rstrip('\n')) for line in lines]
        except Exception as e:
            print(f"Error reading log file: {e}")
            logs = ["Error reading log file"]

    return {
        "running": is_running,
        "startTime": start_time if is_running else None,
        "logs": logs
    }
