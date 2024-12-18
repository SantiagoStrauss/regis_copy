from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    WebDriverException,
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import os
from typing import List, Optional
from dataclasses import dataclass
from contextlib import contextmanager
import traceback
from webdriver_manager.chrome import ChromeDriverManager

# Constants for Chrome setup
DEFAULT_CHROME_PATH = "/opt/render/project/.chrome/chrome-linux64/chrome"
CHROME_BINARY_PATH = os.getenv('CHROME_BINARY', DEFAULT_CHROME_PATH)


@dataclass
class RegistraduriaData:
    nuip: str
    fecha_consulta: Optional[str] = None
    documento: Optional[str] = None  
    estado: Optional[str] = None

class RegistraduriaScraper:
    URL = "https://consultaweb.registraduria.gov.co/censo/_censoResultado.php"
    INPUT_XPATH = "//input[@name='nuip']"
    BUTTON_XPATH = "//button[@type='submit']"

    def __init__(self, headless: bool = True):
        self.logger = self._setup_logger()
        self.verify_chrome_binary()
        self.options = self._setup_chrome_options(headless)
        # Remove version specification to automatically get the matching driver
        self.service = ChromeService(
            ChromeDriverManager(driver_version="131.0.6778.108").install()
        )

    def verify_chrome_binary(self) -> None:
        global CHROME_BINARY_PATH  # Declare global variable before usage
        if not os.path.isfile(CHROME_BINARY_PATH):
            fallback_path = os.path.join(os.getcwd(), "chrome", "chrome.exe")
            if os.path.isfile(fallback_path):
                CHROME_BINARY_PATH = fallback_path
            else:
                self.logger.error(f"Chrome binary not found at {CHROME_BINARY_PATH}")
                raise FileNotFoundError(f"Chrome binary not found at {CHROME_BINARY_PATH}")
        
        if not os.access(CHROME_BINARY_PATH, os.X_OK):
            self.logger.error(f"Chrome binary not executable at {CHROME_BINARY_PATH}")
            raise PermissionError(f"Chrome binary not executable at {CHROME_BINARY_PATH}")

        
        
    @staticmethod
    def _setup_logger() -> logging.Logger:
        logger = logging.getLogger('registraduria_scraper')
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(handler)
        return logger

    @staticmethod
    def _setup_chrome_options(headless: bool) -> webdriver.ChromeOptions:
        options = webdriver.ChromeOptions()
        
        # Essential options for stability
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        if headless:
            options.add_argument('--headless=new')
        
        # Chrome binary path
        options.binary_location = CHROME_BINARY_PATH

        # Performance options
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox') 
        options.add_argument('--disable-software-rasterizer')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # Custom user agent (optional)
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/131.0.6778.108 Safari/537.36'
        )
        return options

    @contextmanager
    def _get_driver(self):
        driver = None
        try:
            driver = webdriver.Chrome(service=self.service, options=self.options)
            driver.maximize_window()
            self.logger.info("Chrome browser started successfully")
            yield driver
        except WebDriverException as e:
            self.logger.error(f"Failed to start Chrome driver: {e}")
            raise
        finally:
            if driver:
                driver.quit()
                self.logger.info("Browser closed")

    def scrape(self, nuip: str) -> Optional[RegistraduriaData]:
        try:
            with self._get_driver() as driver:
                driver.get(self.URL)
                self.logger.info(f"Navigating to {self.URL}")
                
                wait = WebDriverWait(driver, 30)
                
                # Input NUIP
                try:
                    input_field = wait.until(
                        EC.visibility_of_element_located((By.XPATH, self.INPUT_XPATH))
                    )
                    input_field.clear()
                    input_field.send_keys(nuip)
                    self.logger.info(f"NUIP entered: {nuip}")
                    
                    # Click search button
                    search_button = driver.find_element(By.XPATH, self.BUTTON_XPATH)
                    search_button.click()
                    self.logger.info("Search button clicked")
                except TimeoutException:
                    self.logger.error("NUIP field not found within timeout")
                    return None
                except Exception as e:
                    self.logger.error(f"Error entering NUIP or clicking button: {e}")
                    self.logger.error(traceback.format_exc())
                    return None

                # Extract data
                try:
                    results_xpath = '//*[@id="content"]/div[2]/div/div/div/div'
                    result_element = wait.until(
                        EC.visibility_of_element_located((By.XPATH, results_xpath))
                    )
                    
                    # Get consultation date
                    try:
                        fecha_consulta = result_element.find_element(
                            By.XPATH, './/h5[@class="card-title"]'
                        ).text.replace('Fecha Consulta: ', '').strip()
                    except NoSuchElementException:
                        fecha_consulta = None
                        self.logger.error("Consultation date element not found")
                    
                    # Get document number
                    try:
                        documento = result_element.find_element(
                            By.XPATH, './/p[@class="lead"]/span/strong'
                        ).text
                    except NoSuchElementException:
                        documento = None
                        self.logger.error("Document number element not found")
                    
                    # Get status
                    try:
                        estado = result_element.find_elements(
                            By.XPATH, './/p[@class="lead"]/span/strong'
                        )[1].text
                    except (NoSuchElementException, IndexError):
                        estado = None
                        self.logger.error("Status element not found")

                    data = RegistraduriaData(
                        nuip=nuip,
                        fecha_consulta=fecha_consulta,
                        documento=documento,
                        estado=estado
                    )
                    self.logger.info(f"Data extracted: {data}")
                    return data
                    
                except TimeoutException:
                    self.logger.error("Results not found within timeout")
                    return None
                except Exception as e:
                    self.logger.error(f"Error extracting data: {e}")
                    self.logger.error(traceback.format_exc())
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            self.logger.error(traceback.format_exc())
            return None