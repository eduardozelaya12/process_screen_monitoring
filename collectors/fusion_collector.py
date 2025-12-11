import logging
import time
import os
from datetime import datetime
from typing import Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)

class FusionCollector(BaseCollector):
    """
    Coletor para Oracle Fusion/OIC.
    URL hardcoded: https://oic-ajover-produccion-axyh19yueizn-ia.integration.ocp.oraclecloud.com/
    Automação: Login -> Screenshot da tela principal
    """

    def __init__(self, config: Dict):
        super().__init__(config)
        self.base_url = "https://oic-ajover-produccion-axyh19yueizn-ia.integration.ocp.oraclecloud.com/"
        self.credentials = config.get('credentials', {})
        self.timeout = config.get('timeout', 30)
        self.driver = None
        self.headless = config.get('headless', True)

        # Chave do sistema para diretórios únicos (ex: oracle_fusion, oracle_fusion_copy1)
        self._system_key = config.get('_system_key', 'oracle_fusion')

    def update_config(self, config: Dict):
        """Atualiza configuração em tempo de execução"""
        super().update_config(config)
        self.credentials = config.get('credentials', self.credentials)
        self.headless = config.get('headless', self.headless)

    def _init_driver(self):
        """Inicializa WebDriver"""
        if self.driver:
            return

        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless')

        options.add_argument('--start-maximized')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--ignore-certificate-errors')  # Importante para HTTPS self-signed
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(self.timeout)

    def collect(self) -> Dict:
        """Executa o fluxo de coleta do Fusion"""
        try:
            logger.info(f"🚀 Iniciando coleta Oracle Fusion/OIC")
            self._init_driver()

            # 1. Login
            if not self._login():
                return self._mark_error("Falha no Login")

            # 2. Capturar screenshot da tela principal
            screenshot_path, metrics = self._capture_main_screen()

            if not screenshot_path:
                return self._mark_error("Falha ao capturar tela")

            data = {
                'screenshot_path': screenshot_path,
                'metrics': metrics,
                'url': self.base_url
            }
            return self._mark_success(data)

        except Exception as e:
            logger.exception(f"❌ Erro crítico no FusionCollector: {e}")
            return self._mark_error(str(e))
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def _login(self) -> bool:
        """Realiza login no Oracle Fusion/OIC"""
        try:
            logger.info(f"🔐 Acessando login: {self.base_url}")
            self.driver.get(self.base_url)

            username = self.credentials.get('username')
            password = self.credentials.get('password')

            if not username or not password:
                logger.error("❌ Credenciais não fornecidas para Oracle Fusion")
                return False

            # Wait for login form
            wait = WebDriverWait(self.driver, 15)

            # Oracle Fusion/OIC pode usar diferentes seletores para login
            # Tentar primeiro por ID (comum no Oracle)
            try:
                user_input = wait.until(EC.presence_of_element_located((By.ID, "idcs-signin-basic-signin-form-username")))
                pass_input = self.driver.find_element(By.ID, "idcs-signin-basic-signin-form-password")
            except:
                # Fallback para seletores por name
                try:
                    user_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
                    pass_input = self.driver.find_element(By.NAME, "password")
                except:
                    # Tentar por input type
                    user_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[type='email']")))
                    pass_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")

            user_input.clear()
            user_input.send_keys(username)
            pass_input.clear()
            pass_input.send_keys(password)

            # Submit button - tentativa por diferentes seletores
            try:
                submit_btn = self.driver.find_element(By.ID, "idcs-signin-basic-signin-form-submit")
            except:
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                except:
                    try:
                        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    except:
                        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button.signin-button, button.login-button")

            submit_btn.click()

            # Aguardar carregamento da página principal
            time.sleep(8)

            # Verificar se login foi bem sucedido
            current_url = self.driver.current_url.lower()
            if "login" in current_url or "signin" in current_url or "idcs" in current_url:
                logger.error("❌ Falha no login: Permaneceu na página de login")
                return False

            logger.info("✓ Login efetuado com sucesso")
            return True

        except Exception as e:
            logger.error(f"❌ Erro durante login: {e}")
            return False

    def _capture_main_screen(self) -> Tuple[Optional[str], Dict]:
        """Captura screenshot da tela principal após login"""
        try:
            # Aguardar carregamento completo da tela principal
            time.sleep(5)

            # Capturar Screenshot
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_dir = f"storage/screenshots/{self._system_key}"
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = f"{screenshot_dir}/screenshot_{timestamp}.png"

            self.driver.save_screenshot(screenshot_path)
            logger.info(f"📸 Screenshot salvo: {screenshot_path}")

            metrics = {'status': 'collected'}
            return screenshot_path, metrics

        except Exception as e:
            logger.error(f"❌ Erro ao capturar tela: {e}")
            return None, {}

    def test_connection(self) -> bool:
        """Testa se login funciona"""
        try:
            self._init_driver()
            return self._login()
        except Exception:
            return False
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None