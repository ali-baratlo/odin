from apscheduler.schedulers.background import BackgroundScheduler
from collectors.resource_collector import collect_resources
import subprocess
import os

def renew_token():
    # This script's path might need adjustment depending on your project structure
    script_path = '/app/renew_token.sh'
    if os.path.exists(script_path):
        subprocess.call(['/bin/bash', script_path])
    else:
        print(f"Warning: renew_token.sh not found at {script_path}")

def start_scheduler():
    """
    Initializes and starts the background scheduler for periodic tasks.
    The resource collection interval is configurable via an environment variable.
    """
    scheduler = BackgroundScheduler()

    # Schedule the token renewal job (if applicable)
    scheduler.add_job(renew_token, 'interval', hours=24)

    # Get scheduler interval from environment variable, with a default of 1 hour.
    try:
        interval_hours = int(os.getenv("SCHEDULER_INTERVAL_HOURS", "1"))
        if interval_hours <= 0:
            raise ValueError("Interval must be a positive integer.")
    except (ValueError, TypeError):
        print("Invalid or missing SCHEDULER_INTERVAL_HOURS. Defaulting to 1 hour.")
        interval_hours = 1

    # Schedule the resource collection job
    scheduler.add_job(collect_resources, 'interval', hours=interval_hours, id='resource_collector_job')

    scheduler.start()
    print(f"Scheduler started. Resource collection will run every {interval_hours} hour(s).")