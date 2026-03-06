import json
import os
from datetime import datetime
from app.core.config import settings


class TokenLogger:
    def __init__(self):
        log_dir = os.path.dirname(settings.TOKEN_LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

    def log(self, usage: dict):
        """Append token usage to JSONL log file for cost tracking."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            **usage
        }
        with open(settings.TOKEN_LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_totals(self) -> dict:
        """Aggregate total tokens from log file."""
        totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        try:
            with open(settings.TOKEN_LOG_FILE) as f:
                for line in f:
                    entry = json.loads(line)
                    for key in totals:
                        totals[key] += entry.get(key, 0)
        except FileNotFoundError:
            pass
        return totals
