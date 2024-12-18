from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    WebDriverException,
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from typing import Optional
from dataclasses import dataclass
from contextlib import contextmanager
import traceback

@dataclass
class RegistraduriaData:
    nuip: str
    fecha_consulta: Optional[str] = None
    documento: Optional[str] = None
    estado: Optional[str] = None
    # Agrega otros campos relevantes si es necesario
    # Ejemplo:
    # nombre: Optional[str] = None
    # fecha_defuncion: Optional[str] = None

class RegistraduriaScraper:
    URL = 'https://defunciones.registraduria.gov.co/'
    INPUT_XPATH = '//*[@id="nuip"]'
    BUTTON_XPATH = '//*[@id="content"]/div/div/div/div/div[2]/form/div/button'

    def __init__(self, headless: bool = False):
        self.logger = self._setup_logger()
        self.options = self._setup_chrome_options(headless)
        self.service = Service(ChromeDriverManager().install())

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
        if headless:
            options.add_argument('--headless=new')  # Usa el modo headless más reciente
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-webgl') # Deshabilita WebGL
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        # Opcional: Establecer un User-Agent real
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                             'AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/98.0.4758.102 Safari/537.36')
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
                self.logger.info(f"Navegando a {self.URL}")

                wait = WebDriverWait(driver, 30)

                # Ingresar NUIP
                try:
                    input_field = wait.until(
                        EC.visibility_of_element_located((By.XPATH, self.INPUT_XPATH))
                    )
                    input_field.clear()
                    input_field.send_keys(nuip)
                    self.logger.info(f"NUIP ingresado: {nuip}")

                    # Clicar el botón de búsqueda
                    search_button = driver.find_element(By.XPATH, self.BUTTON_XPATH)
                    search_button.click()
                    self.logger.info("Botón de búsqueda clickeado.")
                except TimeoutException:
                    self.logger.error("Campo NUIP no encontrado dentro del tiempo de espera.")
                    return None
                except Exception as e:
                    self.logger.error(f"Error al ingresar NUIP o clicar el botón: {e}")
                    self.logger.error(traceback.format_exc())
                    return None

                # Extraer y procesar los datos necesarios
                try:
                    # Esperar a que los resultados se carguen
                    resultados_xpath = '//*[@id="content"]/div[2]/div/div/div/div'
                    resultado_element = wait.until(
                        EC.visibility_of_element_located((By.XPATH, resultados_xpath))
                    )
                    self.logger.info("Resultados encontrados.")

                    # Extraer Fecha Consulta
                    try:
                        fecha_consulta = resultado_element.find_element(By.XPATH, './/h5[@class="card-title"]').text
                        # Extraer solo la fecha
                        fecha_consulta = fecha_consulta.replace('Fecha Consulta: ', '').strip()
                        self.logger.info(f"Fecha Consulta: {fecha_consulta}")
                    except NoSuchElementException:
                        self.logger.error("Elemento Fecha Consulta no encontrado.")
                        fecha_consulta = None

                    # Extraer Número de Documento
                    try:
                        documento = resultado_element.find_element(By.XPATH, './/p[@class="lead"]/span/strong').text
                        self.logger.info(f"Número de Documento: {documento}")
                    except NoSuchElementException:
                        self.logger.error("Elemento Número de Documento no encontrado.")
                        documento = None

                    # Extraer Estado
                    try:
                        estado = resultado_element.find_elements(By.XPATH, './/p[@class="lead"]/span/strong')[1].text
                        self.logger.info(f"Estado: {estado}")
                    except (NoSuchElementException, IndexError):
                        self.logger.error("Elemento Estado no encontrado.")
                        estado = None

                    # Crear instancia de RegistraduriaData con los datos extraídos
                    data = RegistraduriaData(
                        nuip=nuip,
                        fecha_consulta=fecha_consulta,
                        documento=documento,
                        estado=estado
                    )
                    self.logger.info(f"Datos extraídos: {data}")
                    return data

                except TimeoutException:
                    self.logger.error("Resultados no encontrados dentro del tiempo de espera.")
                    return None
                except Exception as e:
                    self.logger.error(f"Error al extraer datos: {e}")
                    self.logger.error(traceback.format_exc())
                    return None

        except Exception as e:
            self.logger.error(f"Error durante el scraping: {e}")
            self.logger.error(traceback.format_exc())
            return None