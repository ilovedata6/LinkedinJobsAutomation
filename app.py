import os
import logging
import urllib.parse
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables from a .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables
ACCOUNT_EMAIL = os.getenv("ACCOUNT_EMAIL")
ACCOUNT_PASSWORD = os.getenv("ACCOUNT_PASSWORD")
PHONE = os.getenv("NUMBER")
JOB_TITLE = os.getenv("JOB_TITLE", "python")
JOB_LOCATION = os.getenv("JOB_LOCATION", "London, England, United Kingdom")

# Construct the LinkedIn jobs URL
LINKEDIN_JOBS_URL = f"https://www.linkedin.com/jobs/search/?keywords={urllib.parse.quote(JOB_TITLE)}&location={urllib.parse.quote(JOB_LOCATION)}&refresh=true"

def setup_driver():
    """Set up and return the Selenium WebDriver."""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("detach", True)
    chrome_driver_path = ChromeDriverManager().install()
    service = ChromeService(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def login_to_linkedin(driver):
    """Log in to LinkedIn, handling any login modal that appears."""
    driver.get(LINKEDIN_JOBS_URL)

    # Check for and handle the login modal if it appears
    try:
        sign_in_modal_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.sign-in-modal__outlet-btn.cursor-pointer.btn-md.btn-primary.btn-secondary'))
        )
        logging.info("Login modal detected, clicking sign-in button.")
        sign_in_modal_button.click()
    except TimeoutException:
        logging.info("No login modal detected, proceeding with regular login.")

    # Click Reject Cookies Button
    try:
        reject_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'button[action-type="DENY"]'))
        )
        reject_button.click()
    except TimeoutException:
        logging.warning("Could not reject cookies, proceeding without.")

    # Sign in using the modal input fields
    try:
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "base-sign-in-modal_session_key"))
        )
        email_field.send_keys(ACCOUNT_EMAIL)

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "base-sign-in-modal_session_password"))
        )
        password_field.send_keys(ACCOUNT_PASSWORD)
        password_field.send_keys(Keys.ENTER)
    except TimeoutException:
        logging.error("Login fields not found.")
        return



def abort_application(driver):
    """Abort the job application process."""
    try:
        close_button = driver.find_element(By.CLASS_NAME, "artdeco-modal__dismiss")
        close_button.click()
        discard_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "artdeco-modal__confirm-dialog-btn"))
        )
        discard_button.click()
    except (NoSuchElementException, TimeoutException) as e:
        logging.error(f"Error aborting application: {e}")

def apply_to_jobs(driver):
    """Apply to jobs listed on the LinkedIn jobs page, filtering for Easy Apply jobs."""
    try:
        # Click the Easy Apply filter button
        easy_apply_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "searchFilter_applyWithLinkedin"))
        )
        logging.info("Clicking Easy Apply filter button.")
        easy_apply_button.click()

        # Wait for job listings to update
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".job-card-container--clickable"))
        )

        all_listings = driver.find_elements(By.CSS_SELECTOR, ".job-card-container--clickable")

        for listing in all_listings:
            logging.info("Opening Listing")
            listing.click()

            try:
                apply_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-s-apply button"))
                )
                apply_button.click()

                # Enter phone number if empty
                phone_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*=phoneNumber]"))
                )
                if not phone_field.get_attribute("value"):
                    phone_field.send_keys(PHONE)

                # Click Next button
                next_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Next']"))
                )
                next_button.click()

                # Check for Review or Next button
                try:
                    review_button = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Review']"))
                    )
                    review_button.click()

                    # Final submit
                    submit_application_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='Submit application']"))
                    )
                    submit_application_button.click()
                    logging.info("Job application submitted successfully.")

                except TimeoutException:
                    logging.info("Skipping job application due to 'Next' button instead of 'Review'.")
                    abort_application(driver)
                    continue

                close_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "artdeco-modal__dismiss"))
                )
                close_button.click()

            except (NoSuchElementException, TimeoutException) as e:
                logging.error(f"Error applying to job: {e}")
                abort_application(driver)
                continue

    except TimeoutException:
        logging.error("No job listings found.")




def main():
    driver = setup_driver()
    try:
        login_to_linkedin(driver)
        apply_to_jobs(driver)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
