import time
import subprocess
import logging
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_agent_loop():
    logging.info("Starting the Facebook Viral News Agent 24/7 Loop...")
    while True:
        logging.info("Triggering auto_agent.py...")
        try:
            subprocess.run(["python", "auto_agent.py"], check=True)
            logging.info("Agent run completed successfully.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Agent run failed with error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")
            
        base_sleep = 3600
        jitter = random.randint(0, 15 * 60) # 0 to 15 minutes of random jitter
        total_sleep = base_sleep + jitter
        logging.info(f"Waiting for {base_sleep//60} mins plus {jitter//60} mins jitter (Total: {total_sleep//60} mins) before next run...")
        time.sleep(total_sleep)

if __name__ == "__main__":
    run_agent_loop()
