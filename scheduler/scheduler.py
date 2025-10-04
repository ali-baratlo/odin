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
    """
    scheduler = BackgroundScheduler()

    # Schedule the token renewal job (if applicable)
    scheduler.add_job(renew_token, 'interval', hours=24)

    # Schedule the resource collection job to run every 5 minutes
    scheduler.add_job(collect_resources, 'interval', minutes=5, id='resource_collector_job')

    scheduler.start()
    print("Scheduler started. Resource collection will run every 5 minutes.")