import time
import subprocess
import logging

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
            
        logging.info("Waiting for 1 hour before next run...")
        time.sleep(3600)

if __name__ == "__main__":
    run_agent_loop()
