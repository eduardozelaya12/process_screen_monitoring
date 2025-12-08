import logging
import time
import os
from datetime import datetime
from typing import Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)

class BonitaCollector(BaseCollector):
    """
    Coletor para Bonita BPM.
    URL hardcoded: https://dockertst.ajover.com:8445/bonita
    Automação: Login -> Navegar para Casos -> Filtro 'With failures' -> Screenshot
    """

    def __init__(self, config: Dict):
        super().__init__(config)
        self.base_url = "https://dockertst.ajover.com:8445/bonita"
        self.credentials = config.get('credentials', {})
        self.timeout = config.get('timeout', 30)
        self.driver = None
        self.headless = config.get('headless', True)

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
        options.add_argument('--ignore-certificate-errors') # Importante para HTTPS self-signed
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(self.timeout)

    def collect(self) -> Dict:
        """Executa o fluxo de coleta do Bonita"""
        try:
            logger.info(f"🚀 Iniciando coleta Bonita BPM")
            self._init_driver()

            # 1. Login
            if not self._login():
                return self._mark_error("Falha no Login")

            # 2. Navegar e Filtrar
            screenshot_path, metrics = self._navigate_and_capture()
            
            if not screenshot_path:
                return self._mark_error("Falha ao capturar tela")

            data = {
                'screenshot_path': screenshot_path,
                'metrics': metrics,
                'url': self.base_url
            }
            return self._mark_success(data)

        except Exception as e:
            logger.exception(f"❌ Erro crítico no BonitaCollector: {e}")
            return self._mark_error(str(e))
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def _login(self) -> bool:
        """Realiza login no Bonita"""
        try:
            logger.info(f"🔐 Acessando login: {self.base_url}")
            self.driver.get(self.base_url)
            
            username = self.credentials.get('username')
            password = self.credentials.get('password')

            if not username or not password:
                logger.error("❌ Credenciais não fornecidas para Bonita")
                return False

            # Wait for login form
            wait = WebDriverWait(self.driver, 15)
            
            # Seletores genéricos do Bonita (podem precisar de ajuste fino se o tema for customizado)
            # Geralmente input name="username" e name="password"
            user_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            pass_input = self.driver.find_element(By.NAME, "password")
            
            user_input.clear()
            user_input.send_keys(username)
            pass_input.clear()
            pass_input.send_keys(password)
            
            # Submit button - tentativa por type="submit" ou texto
            try:
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            except:
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                
            submit_btn.click()
            
            # Verificar sucesso (esperar URL mudar ou elemento da home)
            time.sleep(5)
            if "login.jsp" in self.driver.current_url:
                logger.error("❌ Falha no login: Permaneceu na página de login")
                return False
                
            logger.info("✓ Login efetuado com sucesso")
            return True

        except Exception as e:
            logger.error(f"❌ Erro durante login: {e}")
            return False

    def _navigate_and_capture(self) -> Tuple[Optional[str], Dict]:
        """Navega para a aplicação, menu Casos e filtra falhas"""
        try:
            wait = WebDriverWait(self.driver, 20)

            # 1. Navegar diretamente para a lista de processos
            target_url = "https://dockertst.ajover.com:8445/bonita/apps/adminAppBonita/admin-process-list/"
            logger.info(f"🔍 Navegando diretamente para: {target_url}")
            self.driver.get(target_url)
            time.sleep(5) # Aguardar carregamento da aplicação

            # 2. Navegar no Menu: BPM -> Casos
            logger.info("🔍 Navegando Menu: BPM -> Casos")
            try:
                # Clicar ou hover no BPM
                bpm_menu = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='BPM'] | //button[normalize-space()='BPM']")))
                bpm_menu.click()
                time.sleep(1)

                # Clicar em Casos (pode estar visível após clique ou hover)
                casos_menu = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Casos'] | //a[normalize-space()='Cases']")))
                casos_menu.click()
                
                logger.info("✓ Acessou menu 'Casos'")
                time.sleep(5) # Aguardar tabela carregar
            except Exception as e:
                logger.error(f"❌ Erro na navegação do menu: {e}")
                self.driver.save_screenshot("storage/logs/bonita_menu_error.png")
                return None, {}

            # 3. Aplicar Filtro 'With failures'
            logger.info("🔍 Aplicando filtro 'With failures'...")
            iframe_switched = False
            try:
                # Verificar se está em um iframe (comum no Bonita)
                frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                if frames:
                    self.driver.switch_to.frame(frames[0])
                    iframe_switched = True
                    logger.info("✓ Switch para iframe detectado")
                
                # Procurar select que contenha opção de falhas
                selects = self.driver.find_elements(By.TAG_NAME, "select")
                filter_applied = False
                
                for select in selects:
                    try:
                        options = select.find_elements(By.TAG_NAME, "option")
                        for opt in options:
                            txt = opt.text.lower()
                            if "failure" in txt or "falha" in txt:
                                Select(select).select_by_visible_text(opt.text)
                                logger.info(f"✓ Filtro aplicado: {opt.text}")
                                filter_applied = True
                                break
                    except:
                        continue
                    if filter_applied: break
                
                if not filter_applied:
                    logger.warning("⚠ Opção 'With failures' não encontrada nos selects. Tentando encontrar drop-down customizado...")
                
                # Aguardar atualização da tabela
                time.sleep(5)

            except Exception as e:
                logger.error(f"❌ Erro ao aplicar filtro: {e}")
            
            # 4. Capturar Screenshot
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            os.makedirs("storage/screenshots/bonita", exist_ok=True)
            screenshot_path = f"storage/screenshots/bonita/screenshot_{timestamp}.png"
            
            # Voltar para contexto default para full page se necessário, mas as vezes o print fica melhor no frame
            if iframe_switched:
                self.driver.switch_to.default_content()
                
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"📸 Screenshot salvo: {screenshot_path}")
            
            metrics = {'status': 'collected'}
            return screenshot_path, metrics

        except Exception as e:
            logger.error(f"❌ Erro na navegação/captura: {e}")
            self.driver.save_screenshot("storage/logs/bonita_error.png")
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
