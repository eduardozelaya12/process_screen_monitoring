import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from typing import Dict, Optional
import logging

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)

class GoogleCollector(BaseCollector):
    """Coletor de exemplo - Navega até o Google"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        self.base_url = config.get('base_url', 'https://www.google.com')
        self.driver = None
        self.timeout = config.get('timeout', 30)
        self.headless = config.get('headless', False)
        self._load_screenshot_preferences(config)
        
        logger.info(f"🔍 GoogleCollector inicializado: {self.system_name}")

    def update_config(self, config: Dict):
        """Atualiza configuração do coletor do Google em runtime"""
        super().update_config(config)

        self.base_url = config.get('base_url', self.base_url)
        self.timeout = config.get('timeout', self.timeout)
        self.headless = config.get('headless', self.headless)
        self._load_screenshot_preferences(config)

        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None

        logger.info("♻️ Configuração do GoogleCollector atualizada")
    
    def _load_screenshot_preferences(self, config: Dict):
        screenshot_cfg = (config or {}).get('screenshot') or {}

        def _safe_int(value, default, minimum=None):
            try:
                if value is None:
                    raise ValueError()
                parsed = int(value)
                if minimum is not None and parsed < minimum:
                    raise ValueError()
                return parsed
            except (ValueError, TypeError):
                return default

        self.screenshot_width = _safe_int(screenshot_cfg.get('width'), 1920, minimum=600)
        self.screenshot_height = _safe_int(screenshot_cfg.get('height'), 1080, minimum=400)
        full_page = screenshot_cfg.get('full_page', False)
        self.full_page_screenshot = full_page if isinstance(full_page, bool) else False
        logger.info(
            f"🖼️ Preferências de screenshot (Google): {self.screenshot_width}x{self.screenshot_height} | full_page={self.full_page_screenshot}"
        )

    def _configure_viewport(self):
        if not self.driver:
            return
        try:
            self.driver.set_window_size(self.screenshot_width, self.screenshot_height)
        except Exception as e:
            logger.debug(f"Falha ao ajustar viewport do GoogleCollector: {e}")

    def _prepare_full_page_capture(self):
        if not self.driver or not self.full_page_screenshot:
            return
        try:
            total_width = self.driver.execute_script(
                "return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth, "
                "document.documentElement.clientWidth);"
            )
            total_height = self.driver.execute_script(
                "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, "
                "document.documentElement.clientHeight);"
            )
            width = max(int(total_width or 0), self.screenshot_width)
            height = max(int(total_height or 0), self.screenshot_height)
            if width and height:
                self.driver.set_window_size(width, height)
        except Exception as e:
            logger.debug(f"Falha ao preparar captura full-page Google: {e}")
    
    def test_connection(self) -> bool:
        """Testa conexão com o Google"""
        try:
            import requests
            response = requests.get(self.base_url, timeout=5)
            return response.status_code == 200
        except:
            return True  # Assume que está OK
    
    def collect(self) -> Dict:
        """Coleta dados do Google - Screenshot da página inicial"""
        try:
            logger.info(f"📸 Coletando dados: {self.system_name}")
            
            screenshot_path = self._capture_screenshot()
            
            if not screenshot_path:
                return self._mark_error("Falha ao capturar screenshot")
            
            data = {
                'screenshot_path': screenshot_path,
                'url': self.base_url,
                'status': 'online'
            }
            
            return self._mark_success(data)
            
        except Exception as e:
            logger.exception(f"❌ Erro na coleta: {e}")
            return self._mark_error(str(e))
    
    def _capture_screenshot(self) -> Optional[str]:
        """Captura screenshot da página do Google"""
        try:
            self._init_driver()
            
            logger.info(f"Navegando para: {self.base_url}")
            self.driver.get(self.base_url)
            time.sleep(2)
            
            # Aguardar logo do Google carregar
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "img[alt='Google']"))
                )
                logger.info("✓ Página Google carregada")
            except:
                logger.warning("⚠ Logo do Google não encontrado")
            
            # Salvar screenshot
            screenshot_dir = "storage/screenshots/google"
            os.makedirs(screenshot_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{screenshot_dir}/screenshot_{timestamp}.png"
            
            self._prepare_full_page_capture()
            captured = False
            if self.full_page_screenshot and hasattr(self.driver, "get_full_page_screenshot_as_file"):
                try:
                    self.driver.get_full_page_screenshot_as_file(screenshot_path)
                    captured = True
                except Exception as e:
                    logger.debug(f"Falha ao usar full page screenshot (Google): {e}")
            if not captured:
                self.driver.save_screenshot(screenshot_path)
            logger.info(f"✓ Screenshot salvo: {screenshot_path}")
            
            return screenshot_path
            
        except Exception as e:
            logger.error(f"❌ Erro ao capturar screenshot: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def _init_driver(self):
        """Inicializa WebDriver"""
        if self.driver:
            return
        
        options = webdriver.ChromeOptions()
        
        # Modo headless configurável
        if self.headless:
            options.add_argument('--headless')
            logger.info("🎭 Modo HEADLESS ativado")
        else:
            options.add_argument('--start-maximized')
            logger.info("👀 Modo VISUAL ativado")
        
        options.add_argument(f'--window-size={self.screenshot_width},{self.screenshot_height}')
        options.add_argument('--force-device-scale-factor=1')
        options.add_argument('--hide-scrollbars')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(self.timeout)
        self._configure_viewport()
        logger.info("✓ WebDriver inicializado")
    
    def cleanup(self):
        """Limpa recursos"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
