import time
import logging
import pylast

# Configure logging to display the error messages
logging.basicConfig(level=logging.ERROR)

def main():
    # Your main function code here
    print("Running main function")
    # Simulate an error for demonstration purposes
    raise pylast.WSError("Simulated WSError")

if __name__ == "__main__":
    while True:  # Loop to keep the script running
        try:
            main()
        except pylast.WSError as e:
            logging.error(f"Encountered a WSError: {e}. Restarting in 10 seconds...")
            time.sleep(10)  # Wait 10 seconds before restarting
        except Exception as e:
            logging.error(f"Unexpected error: {e}. Restarting in 10 seconds...")
            time.sleep(10)  # Wait 10 seconds before restarting
