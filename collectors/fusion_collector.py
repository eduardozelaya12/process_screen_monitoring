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

class FusionCollector(BaseCollector):
    """Coletor de Oracle Fusion/OIC - Captura screenshot da tela principal"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        # URL fixa do Oracle Fusion/OIC
        self.base_url = "https://oic-ajover-produccion-axyh19yueizn-ia.integration.ocp.oraclecloud.com/"
        self.credentials = config.get('credentials', {})
        self.driver = None
        self.timeout = config.get('timeout', 30)
        self.headless = config.get('headless', True)
        self._system_key = config.get('_system_key', 'oracle_fusion')
        self._load_screenshot_preferences(config)
        
        logger.info(f"🔍 FusionCollector inicializado: {self.system_name}")

    def update_config(self, config: Dict):
        """Atualiza configuração do coletor em runtime"""
        super().update_config(config)

        self.credentials = config.get('credentials', self.credentials)
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

        logger.info("♻️ Configuração do FusionCollector atualizada")
    
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

    def _configure_viewport(self):
        if not self.driver:
            return
        try:
            self.driver.set_window_size(self.screenshot_width, self.screenshot_height)
        except Exception as e:
            logger.debug(f"Falha ao ajustar viewport: {e}")

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
            logger.debug(f"Falha ao preparar captura full-page: {e}")
    
    def test_connection(self) -> bool:
        """Testa conexão com Oracle Fusion"""
        try:
            import requests
            response = requests.get(self.base_url, timeout=10, verify=False)
            return response.status_code in [200, 302, 401, 403]  # Qualquer resposta indica que está online
        except:
            return False
    
    def collect(self) -> Dict:
        """Coleta dados do Oracle Fusion - Login e Screenshot da página principal"""
        try:
            logger.info(f"📸 Coletando dados: {self.system_name}")
            
            self._init_driver()
            
            # Tentar fazer login se credenciais disponíveis
            login_success = self._login()
            
            if login_success:
                # Aguardar tela principal carregar antes de tirar screenshot
                self._wait_for_main_page()
            
            # Capturar screenshot
            screenshot_path = self._capture_screenshot()
            
            if not screenshot_path:
                return self._mark_error("Falha ao capturar screenshot")
            
            data = {
                'screenshot_path': screenshot_path,
                'url': self.base_url,
                'status': 'online' if login_success else 'login_required',
                'login_success': login_success
            }
            
            return self._mark_success(data)
            
        except Exception as e:
            logger.exception(f"❌ Erro na coleta: {e}")
            return self._mark_error(str(e))
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
    
    def _wait_for_main_page(self):
        """Aguarda login, navega ao dashboard de monitoramento e aguarda gráficos carregarem"""
        try:
            logger.info("⏳ Verificando se login foi concluído...")
            
            wait = WebDriverWait(self.driver, 30)
            
            # PASSO 1: Verificar se chegou na página do Oracle (logo ORACLE visível)
            oracle_indicators = [
                (By.XPATH, "//*[contains(text(), 'ORACLE')]"),
                (By.XPATH, "//*[contains(text(), 'Criar e monitorar')]"),
                (By.CSS_SELECTOR, "[class*='oracle']"),
            ]
            
            oracle_loaded = False
            for by, selector in oracle_indicators:
                try:
                    wait.until(EC.presence_of_element_located((by, selector)))
                    logger.info(f"✓ Página Oracle detectada: {selector}")
                    oracle_loaded = True
                    break
                except:
                    continue
            
            if not oracle_loaded:
                logger.warning("⚠ Página Oracle não detectada")
                time.sleep(5)
                return False
            
            # PASSO 2: Navegar para o Dashboard de Monitoramento
            dashboard_url = "https://design.integration.us-ashburn-1.ocp.oraclecloud.com/?root=monitoringDashboard&integrationInstance=oic-ajover-produccion-axyh19yueizn-ia"
            logger.info(f"🔗 Navegando para Dashboard de Monitoramento...")
            self.driver.get(dashboard_url)
            time.sleep(5)  # Aguardar redirecionamento inicial
            
            # PASSO 3: Aguardar gráficos/dashboard carregar
            logger.info("⏳ Aguardando dashboard carregar...")
            
            dashboard_indicators = [
                (By.XPATH, "//*[contains(text(), 'Painel de controle de integrações')]"),
                (By.XPATH, "//*[contains(text(), 'Integration Dashboard')]"),
                (By.XPATH, "//*[contains(text(), 'Status da instância')]"),
                (By.XPATH, "//*[contains(text(), 'Instance Status')]"),
                (By.XPATH, "//*[contains(text(), 'Visão Geral')]"),
                (By.XPATH, "//*[contains(text(), 'Overview')]"),
                (By.XPATH, "//*[contains(text(), 'Taxa de erros')]"),
                (By.XPATH, "//*[contains(text(), 'Integrações ativas')]"),
                (By.CSS_SELECTOR, "[class*='chart']"),
                (By.CSS_SELECTOR, "[class*='graph']"),
                (By.CSS_SELECTOR, "svg"),  # Gráficos geralmente são SVG
            ]
            
            for by, selector in dashboard_indicators:
                try:
                    element = wait.until(EC.presence_of_element_located((by, selector)))
                    logger.info(f"✓ Dashboard carregado: {selector}")
                    time.sleep(3)  # Aguardar gráficos renderizarem completamente
                    return True
                except:
                    continue
            
            # Se não encontrou indicadores específicos, aguardar tempo genérico
            logger.warning("⚠ Indicadores do dashboard não encontrados, aguardando 8s...")
            time.sleep(8)
            return True
            
        except Exception as e:
            logger.warning(f"⚠ Erro ao aguardar dashboard: {e}")
            time.sleep(5)
            return False
            time.sleep(5)
            return False

    def _login(self) -> bool:
        """Realiza login no Oracle Fusion/OIC via Azure AD SSO"""
        try:
            username = self.credentials.get('username')  # Email do usuário
            password = self.credentials.get('password')
            
            if not username or not password:
                logger.warning("⚠ Credenciais não configuradas para Fusion - acessando sem login")
                self.driver.get(self.base_url)
                time.sleep(3)
                return False
            
            logger.info(f"🔐 Acessando: {self.base_url}")
            self.driver.get(self.base_url)
            
            # Aguardar página Oracle Cloud carregar
            time.sleep(5)
            
            wait = WebDriverWait(self.driver, 30)
            
            # ========================================
            # PASSO 1: Clicar no botão "AzureAD"
            # ========================================
            logger.info("🔍 Procurando botão AzureAD...")
            azure_ad_btn = None
            azure_selectors = [
                (By.XPATH, "//button[contains(text(), 'AzureAD')]"),
                (By.XPATH, "//a[contains(text(), 'AzureAD')]"),
                (By.XPATH, "//*[contains(text(), 'AzureAD')]"),
                (By.CSS_SELECTOR, "button[data-idp='AzureAD']"),
                (By.CSS_SELECTOR, "[class*='azure']"),
                (By.XPATH, "//button[contains(@class, 'idp')]"),
            ]
            
            for by, selector in azure_selectors:
                try:
                    azure_ad_btn = wait.until(EC.element_to_be_clickable((by, selector)))
                    logger.info(f"✓ Botão AzureAD encontrado: {selector}")
                    break
                except:
                    continue
            
            if not azure_ad_btn:
                logger.warning("⚠ Botão AzureAD não encontrado - tentando login direto Oracle")
                return self._login_oracle_direct()
            
            # Clicar no botão AzureAD
            azure_ad_btn.click()
            logger.info("✓ Clicou no botão AzureAD")
            time.sleep(5)  # Aguardar redirecionamento para Microsoft
            
            # ========================================
            # PASSO 2: Identificar tela Microsoft e agir
            # ========================================
            logger.info(f"🔍 Identificando tela Microsoft...")
            
            try:
                # Verificar se é a tela "Entrar" (digitar email) ou "Escolha uma conta" (clicar)
                page_title = self.driver.title.lower()
                logger.info(f"📄 Título da página: {self.driver.title}")
                
                # Cenário 1: Tela "Entrar em sua conta" - precisa digitar o email
                if "entrar" in page_title or "sign in" in page_title:
                    logger.info("📝 Tela 'Entrar' detectada - digitando email...")
                    
                    # Encontrar campo de email
                    email_input = wait.until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "input[type='email'], input[name='loginfmt'], input[type='text']")
                    ))
                    email_input.clear()
                    email_input.send_keys(username)
                    logger.info(f"✓ Email digitado: {username}")
                    time.sleep(1)
                    
                    # Clicar em Avançar/Next
                    avancar_btn = wait.until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                    ))
                    avancar_btn.click()
                    logger.info("✓ Clicou em Avançar")
                    time.sleep(3)
                
                # Cenário 2: Tela "Escolha uma conta" - clicar na conta
                elif "escolha" in page_title or "pick" in page_title or "choose" in page_title:
                    logger.info("� Tela 'Escolha uma conta' detectada - procurando conta...")
                    
                    account_element = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, f"//*[contains(text(), '{username}')]")
                    ))
                    account_element.click()
                    logger.info(f"✓ Clicou na conta: {username}")
                    time.sleep(3)
                
                # Cenário 3: Não identificou o título - tentar encontrar campo de email ou conta
                else:
                    logger.info("🔍 Título não reconhecido, tentando detectar elementos...")
                    
                    # Primeiro tenta encontrar campo de email (tela de Entrar)
                    try:
                        email_input = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "input[type='email'], input[name='loginfmt']")
                        ))
                        email_input.clear()
                        email_input.send_keys(username)
                        logger.info(f"✓ Email digitado: {username}")
                        
                        avancar_btn = wait.until(EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                        ))
                        avancar_btn.click()
                        logger.info("✓ Clicou em Avançar")
                        time.sleep(3)
                    except:
                        # Se não encontrou email, tenta encontrar conta listada
                        try:
                            account_element = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(
                                (By.XPATH, f"//*[contains(text(), '{username}')]")
                            ))
                            account_element.click()
                            logger.info(f"✓ Clicou na conta: {username}")
                            time.sleep(3)
                        except:
                            logger.warning("⚠ Não foi possível identificar email ou conta")
                
            except Exception as e:
                logger.warning(f"⚠ Erro ao identificar tela Microsoft: {e}")
            
            # ========================================
            # PASSO 3: Digitar senha no Microsoft
            # ========================================
            logger.info("🔍 Procurando campo de senha Microsoft...")
            
            try:
                # Aguardar campo de senha aparecer
                pass_input = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "input[type='password'], input[name='passwd']")
                ))
                logger.info("✓ Campo de senha encontrado")
                
                pass_input.clear()
                pass_input.send_keys(password)
                logger.info("✓ Senha digitada")
                time.sleep(0.5)
                
                # Clicar em Entrar/Sign in
                signin_btn = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
                ))
                signin_btn.click()
                logger.info("✓ Clicou em Entrar")
                time.sleep(5)
                
                # Verificar se há opção "Continuar conectado?" e clicar em "Sim"
                try:
                    # Esperar a tela aparecer (pode demorar um pouco)
                    sim_btn = WebDriverWait(self.driver, 8).until(EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Sim')] | //input[@value='Sim'] | //button[contains(text(), 'Yes')] | //input[@value='Yes']")
                    ))
                    sim_btn.click()
                    logger.info("✓ Clicou em 'Sim' para continuar conectado")
                    time.sleep(3)
                except:
                    logger.info("ℹ Tela 'Continuar conectado' não apareceu ou já passou")
                
            except Exception as e:
                logger.error(f"❌ Erro ao digitar senha: {e}")
                return False
            
            # Aguardar redirecionamento de volta para Oracle
            time.sleep(5)
            
            # Verificar se login foi bem sucedido
            current_url = self.driver.current_url.lower()
            if "login" in current_url or "signin" in current_url or "microsoftonline" in current_url:
                logger.warning("⚠ Login pode ter falhado - ainda na página de login")
                return False
            
            logger.info("✓ Login via Azure AD efetuado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro durante login: {e}")
            return False
    
    def _login_oracle_direct(self) -> bool:
        """Fallback: Login direto no Oracle (sem Azure AD)"""
        try:
            wait = WebDriverWait(self.driver, 15)
            username = self.credentials.get('username')
            password = self.credentials.get('password')
            
            # Procurar campos de login Oracle
            user_input = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[name='username']")
            ))
            user_input.clear()
            user_input.send_keys(username)
            
            pass_input = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[type='password']")
            ))
            pass_input.clear()
            pass_input.send_keys(password)
            
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            submit_btn.click()
            
            time.sleep(5)
            return True
        except Exception as e:
            logger.error(f"❌ Erro no login direto Oracle: {e}")
            return False
    
    def _capture_screenshot(self) -> Optional[str]:
        """Captura screenshot da página atual"""
        try:
            # Verificar se driver existe
            if not self.driver:
                logger.error("❌ Driver não disponível para captura de screenshot")
                return None
            
            # Aguardar página carregar
            time.sleep(2)
            
            # Usar _system_key para diretório único
            screenshot_dir = f"storage/screenshots/{self._system_key}"
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
                    logger.debug(f"Falha full page screenshot: {e}")
            
            if not captured:
                self.driver.save_screenshot(screenshot_path)
            
            logger.info(f"📸 Screenshot salvo: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"❌ Erro ao capturar screenshot: {e}")
            return None
    
    def _init_driver(self):
        """Inicializa WebDriver"""
        if self.driver:
            return
        
        options = webdriver.ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless')
            logger.info("🎭 Modo HEADLESS ativado")
        else:
            options.add_argument('--start-maximized')
            logger.info("👀 Modo VISUAL ativado")
        
        options.add_argument(f'--window-size={self.screenshot_width},{self.screenshot_height}')
        options.add_argument('--force-device-scale-factor=1')
        options.add_argument('--ignore-certificate-errors')  # Importante para HTTPS
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
