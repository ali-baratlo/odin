from apscheduler.schedulers.background import BackgroundScheduler
import subprocess

def renew_token():
    subprocess.call(['/bin/bash', '/app/renew_token.sh'])

scheduler = BackgroundScheduler()
scheduler.add_job(renew_token, 'interval', hours=24)    
scheduler.start()