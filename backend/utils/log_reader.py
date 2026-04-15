"""
Utility module for reading and sanitizing crawler logs
"""

import os
import re
import json
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


def parse_log_timestamp(line):
    """Parse timestamp from log line like '[2026-04-15 21:17:19]'."""
    match = re.match(r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]', line)
    if match:
        try:
            return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
    return None


def read_status_file(status_file_path):
    """
    Read crawler status file.
    Returns dict with status info or None if file doesn't exist.
    """
    if not os.path.exists(status_file_path):
        return None
    try:
        with open(status_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def read_fetch_log(log_file_path, offset=0, status_file_path=None):
    """
    Read fetch log file and return sanitized content with offset support.

    Args:
        log_file_path: Path to the crawler log file
        offset: Number of lines to skip (for pagination/streaming)
        status_file_path: Optional path to status JSON file for accurate state

    Returns:
        dict: {
            "running": bool,
            "isComplete": bool,
            "isFailed": bool,
            "startTime": str (ISO format) or None,
            "endTime": str (ISO format) or None,
            "elapsedSeconds": int or None,
            "logs": list of sanitized log lines,
            "totalLines": int (total lines in file),
            "offset": int (the offset that was requested)
        }
    """
    # Check if log file exists
    if not os.path.exists(log_file_path):
        return {
            "running": False,
            "isComplete": False,
            "isFailed": False,
            "startTime": None,
            "endTime": None,
            "elapsedSeconds": None,
            "logs": [],
            "totalLines": 0,
            "offset": offset
        }

    # Read status file - required for accurate state detection
    if not status_file_path:
        return {
            "running": False,
            "isComplete": False,
            "isFailed": False,
            "startTime": None,
            "endTime": None,
            "elapsedSeconds": None,
            "logs": [],
            "totalLines": 0,
            "offset": offset,
            "error": "Status file path not configured"
        }

    status = read_status_file(status_file_path)
    if not status:
        # Status file doesn't exist - update not running or status corrupted
        return {
            "running": False,
            "isComplete": False,
            "isFailed": False,
            "startTime": None,
            "endTime": None,
            "elapsedSeconds": None,
            "logs": [],
            "totalLines": 0,
            "offset": offset
        }

    # Read all lines
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            total_lines = len(lines)
    except Exception as e:
        print(f"Error reading log file: {e}")
        return {
            "running": status.get("status") == "running",
            "isComplete": status.get("status") == "completed",
            "isFailed": status.get("status") == "failed",
            "startTime": status.get("startTime"),
            "endTime": status.get("endTime"),
            "elapsedSeconds": None,
            "logs": ["Error reading log file"],
            "totalLines": 0,
            "offset": offset
        }

    # Use status file for accurate state
    is_running = status.get("status") == "running"
    is_complete = status.get("status") == "completed"
    is_failed = status.get("status") == "failed"
    start_time_str = status.get("startTime")
    end_time_str = status.get("endTime")

    # Parse start time
    start_time = None
    if start_time_str:
        try:
            start_time = datetime.fromisoformat(start_time_str)
        except ValueError:
            pass

    # Parse end time
    end_time = None
    if end_time_str:
        try:
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            pass

    # Calculate elapsed time
    if is_running and start_time:
        elapsed_seconds = int((datetime.now() - start_time).total_seconds())
    elif end_time and start_time:
        elapsed_seconds = int((end_time - start_time).total_seconds())
    else:
        elapsed_seconds = 0

    # Get lines from offset
    lines_from_offset = lines[offset:] if offset < total_lines else []

    # Sanitize each line
    logs = [sanitize_log_line(line.rstrip('\n')) for line in lines_from_offset]

    return {
        "running": is_running,
        "isComplete": is_complete,
        "isFailed": is_failed,
        "startTime": start_time.isoformat() if start_time else None,
        "endTime": end_time.isoformat() if end_time else None,
        "elapsedSeconds": elapsed_seconds,
        "logs": logs,
        "totalLines": total_lines,
        "offset": offset
    }
