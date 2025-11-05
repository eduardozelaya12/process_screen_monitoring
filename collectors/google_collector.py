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
        
        logger.info(f"🔍 GoogleCollector inicializado: {self.system_name}")
    
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
        
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(self.timeout)
        logger.info("✓ WebDriver inicializado")
    
    def cleanup(self):
        """Limpa recursos"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
