import pickle
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, NoSuchElementException
# substituído: evitar dependência direta para prevenir NameError em execuções específicas
import traceback
from selenium.common import exceptions as sel_ex
import urllib.parse
from datetime import datetime
from typing import Dict, Optional, List
import logging

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)

class PeopleSoftCollector(BaseCollector):
    """Coletor de dados do PeopleSoft via Selenium"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        
        self.base_url = config['base_url']
        self.process_url = config.get('process_monitor_url', self.base_url)
        self.cookies_file = "config/credentials/peoplesoft_cookies.pkl"
        self.credentials = config.get('credentials', {})
        self.driver = None
        self.timeout = config.get('timeout', 30)
    
    def collect(self) -> Dict:
        """Coleta dados do PeopleSoft"""
        try:
            logger.info(f"📸 Coletando dados: {self.system_name}")
            
            # Verificar se cookies existem
            if not os.path.exists(self.cookies_file):
                logger.warning("⚠ Cookies não encontrados. Tentando fazer login...")
                if not self.login_and_save_cookies():
                    return self._mark_error("Falha no login inicial")
            
            # Capturar screenshot e extrair dados
            screenshot_path, metrics = self._capture_and_extract()
            
            if not screenshot_path:
                # Tentar relogin se falhou
                logger.warning("⚠ Falha na captura. Tentando relogin...")
                if self.login_and_save_cookies():
                    screenshot_path, metrics = self._capture_and_extract()
                
                if not screenshot_path:
                    return self._mark_error("Falha ao capturar screenshot após relogin")
            
            data = {
                'screenshot_path': screenshot_path,
                'metrics': metrics,
                'url': self.process_url
            }
            
            return self._mark_success(data)
            
        except Exception as e:
            logger.exception(f"❌ Erro na coleta: {e}")
            return self._mark_error(str(e))
    
    def test_connection(self) -> bool:
        """Testa conexão com PeopleSoft"""
        try:
            self._init_driver()
            self.driver.get(self.base_url)
            time.sleep(2)
            is_accessible = "peoplesoft" in self.driver.title.lower() or "sign in" in self.driver.page_source.lower()
            return is_accessible
        except Exception as e:
            logger.error(f"Erro ao testar conexão: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def _init_driver(self):
        """Inicializa WebDriver"""
        if self.driver:
            return
        
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        # options.add_argument('--headless')  # Rodar sem interface gráfica
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(self.timeout)
        logger.info("✓ WebDriver inicializado")
    
    def _load_cookies(self) -> bool:
        """Carrega cookies salvos"""
        try:
            if not os.path.exists(self.cookies_file):
                return False
            
            self.driver.get(self.base_url)
            time.sleep(2)
            
            with open(self.cookies_file, "rb") as f:
                cookies = pickle.load(f)
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Erro ao adicionar cookie: {e}")
            
            self.driver.refresh()
            time.sleep(2)
            
            # Verificar se ainda está na página de login
            if "signon" in self.driver.current_url.lower():
                logger.warning("⚠ Cookies expirados")
                return False
            
            logger.info("✓ Cookies carregados")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar cookies: {e}")
            return False
    
    def _capture_and_extract(self) -> tuple[Optional[str], Dict]:
        """Captura screenshot e extrai métricas"""
        try:
            self._init_driver()
            
            # Carregar cookies
            if not self._load_cookies():
                return None, {}
            
            # Navegar para página de processos
            logger.info(f"Navegando para: {self.process_url}")
            self.driver.get(self.process_url)
            time.sleep(3)
            
            # Log útil para debugging
            try:
                current_url = self.driver.current_url
                logger.info(f"URL atual após navegação: {current_url}")
                # ... código anterior ...

                logger.info(f"🛠 Após tentativa de navegação, URL atual: {self.driver.current_url}")

                # Sanity check: Verificar se está no host esperado e no path do Monitor
                url_ok = True
                expected_host = urllib.parse.urlparse(self.process_url).hostname
                current_host = urllib.parse.urlparse(self.driver.current_url).hostname
                expected_path = urllib.parse.urlparse(self.process_url).path
                current_path = urllib.parse.urlparse(self.driver.current_url).path

                if current_host != expected_host:
                    logger.error(f"❌ HOST INCORRETO: esperado={expected_host} obtido={current_host} | Abandonando coleta!")
                    url_ok = False

                # PeopleSoft pode redirecionar para login em caminho totalmente diferente (ex. "/psp/pa91test/EMPLOYEE/EMPL/h/")
                if not current_path.lower().endswith(expected_path.lower()):
                    logger.error(f"❌ PATH inesperado: esperado termina com={expected_path} obtido={current_path}")
                    url_ok = False

                # Opcional: Verifica se está na tela de login usando trechos típicos do title ou da página
                page_title = self.driver.title.lower()
                if any(sub in page_title for sub in ["login", "sign on", "autenticação"]):
                    logger.error("❌ Navegação levou para tela de login! O cookie ou sessão foi perdida!")
                    url_ok = False

                if not url_ok:
                    logger.error(f"""
                    [SANITY CHECK FALHOU]
                    - Esperado: {self.process_url}
                    - Obtido  : {self.driver.current_url}
                    - Host ok?: {current_host == expected_host}
                    - Path ok?: {current_path.lower().endswith(expected_path.lower())}
                    - Título  : {page_title}
                    - Abandonando extração e salvando screenshot/html para debug.
                    """)
                    # Printar o HTML inteiro para depuração futura
                    html_path = os.path.join("storage", "logs", "page_structure_wrong_url.html")
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    self.driver.save_screenshot("storage/logs/screenshot_wrong_url.png")
                    return None, {}

                logger.info("✓ URL ok - prosseguindo para extrair métricas!")

            except Exception:
                logger.debug("Não foi possível ler current_url")

            # Detectar redirecionamento para login/host diferente e tentar relogin+retry
            def _is_login_like(url: str) -> bool:
                if not url:
                    return False
                lu = url.lower()
                login_indicators = ('cmd=login', '/h/?cmd=login', 'signon', 'errorcode=', '/psp/pa')
                if any(tok in lu for tok in login_indicators):
                    return True
                try:
                    base_host = urllib.parse.urlparse(self.base_url).hostname or ''
                    cur_host = urllib.parse.urlparse(lu).hostname or ''
                    if base_host and cur_host and base_host != cur_host:
                        return True
                except Exception:
                    pass
                return False

            try:
                if _is_login_like(self.driver.current_url):
                    logger.warning("⚠ Detectado redirecionamento para login/host diferente: %s", self.driver.current_url)
                    try:
                        os.makedirs("storage/logs", exist_ok=True)
                        html_path = os.path.join("storage", "logs", "page_structure.html")
                        with open(html_path, "w", encoding="utf-8") as f:
                            f.write(self.driver.page_source)
                        logger.warning("✓ page_source salvo em %s", html_path)
                    except Exception as e:
                        logger.debug("Falha salvando page_source: %s", e)

                    logger.info("↻ Tentando relogin automático e nova navegação...")
                    if self.login_and_save_cookies():
                        # login_and_save_cookies finaliza o driver atual; reinicia e carrega cookies
                        if self.driver:
                            try:
                                self.driver.quit()
                            except Exception:
                                pass
                            self.driver = None
                        self._init_driver()
                        if self._load_cookies():
                            logger.info("✓ Cookies recarregados após relogin, tentando navegar novamente")
                            self.driver.get(self.process_url)
                            time.sleep(4)
                            try:
                                logger.info("URL atual após retry: %s", self.driver.current_url)
                            except Exception:
                                pass
                        else:
                            logger.error("❌ Falha ao recarregar cookies após relogin")
                            return None, {}
                    else:
                        logger.error("❌ Relogin automático falhou; abortando extração")
                        return None, {}
            except Exception:
                logger.exception("Erro durante verificação de redirecionamento/login")
            
            # Listar frames/iframes disponíveis (útil para detectar ptifrmtgtframe)
            try:
                frames = self.driver.find_elements(By.TAG_NAME, "iframe") + self.driver.find_elements(By.TAG_NAME, "frame")
                frame_info = []
                for f in frames:
                    try:
                        frame_info.append({
                            'id': f.get_attribute('id'),
                            'name': f.get_attribute('name'),
                            'src': f.get_attribute('src')
                        })
                    except Exception:
                        continue
                logger.info(f"Frames encontrados: {frame_info}")
            except Exception:
                logger.debug("Não foi possível listar frames")

            # --- ADICIONADO: continuar fluxo de extração (limpar filtros, extrair métricas e salvar screenshot)
            try:
                # Limpar possíveis filtros e forçar refresh da grid
                self._clear_name_filter()
                time.sleep(4)

                # Extrair métricas da página (irá salvar page_source se a tabela não for encontrada)
                metrics = self._extract_metrics_from_page()

                # Salvar screenshot
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_dir = f"storage/screenshots/peoplesoft"
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = f"{screenshot_dir}/screenshot_{timestamp}.png"
                try:
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"✓ Screenshot salvo: {screenshot_path}")
                except Exception as e:
                    logger.warning(f"Falha ao salvar screenshot: {e}")
                    screenshot_path = ""

                return screenshot_path, metrics

            except Exception as e:
                logger.error(f"❌ Erro no fluxo de extração: {e}\n{traceback.format_exc()}")
                return None, {}

        except Exception as e:
            logger.error(f"❌ Erro ao capturar: {e}\n{traceback.format_exc()}")
            return None, {}
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def _clear_name_filter(self):
        """Limpa filtro de nome e clica refresh"""
        try:
            # Tentar limpar campo de nome
            try:
                campo_nome = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "PMN_FILTER_WRK_PRCSNAME"))
                )
                campo_nome.clear()
                campo_nome.send_keys(Keys.CONTROL, "a")
                campo_nome.send_keys(Keys.BACKSPACE)
                logger.info("✓ Campo de nome limpo")
            except Exception as e:
                logger.debug(f"Campo de nome não encontrado ou erro: {type(e).__name__} - {e}")
            
            # Clicar refresh
            try:
                botao_refresh = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "REFRESH_BTN"))
                )
                self.driver.execute_script("arguments[0].click();", botao_refresh)
                logger.info("✓ Botão refresh clicado")
            except Exception as e:
                logger.debug(f"Botão refresh não encontrado ou erro: {type(e).__name__} - {e}")
            
        except Exception as e:
            logger.warning(f"⚠ Erro ao limpar filtros: {type(e).__name__} - {e}")
    
    def _extract_metrics_from_page(self) -> Dict:
        """
        Extrai métricas da página do Process Monitor
        Tenta extrair dados reais da tabela HTML
        """
        try:
            # Aguardar tabela carregar
            time.sleep(2)
            
            metrics = {
                'total_processes': 0,
                'running': 0,
                'failed': 0,
                'success': 0,
                'success_rate': 100.0,
                'critical_errors': []
            }
            
            # Tentar encontrar tabela de processos
            try:
                # Seletores comuns para tabelas PeopleSoft
                table_selectors = [
                    "table[id*='PROCESS']",
                    "table.PSLEVEL1GRID",
                    "table.PSLEVEL1GRIDWBO",
                    "div[id*='divPROCESS'] table",
                    "table[summary*='Process']",
                    "table[summary*='Process List']"
                ]
                
                table = None
                for selector in table_selectors:
                    try:
                        logger.debug(f"Tentando selector: {selector}")
                        table = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if table:
                            logger.info(f"✓ Tabela encontrada com selector: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} não encontrou tabela: {type(e).__name__} - {e}")
                        continue
                
                # Se não encontrou, tentar procurar linhas por XPath que capturem grid interno
                if not table:
                    try:
                        possible = self.driver.find_elements(By.XPATH, "//table//tr")
                        logger.debug(f"Encontradas {len(possible)} <tr> em todo o documento (fallback)")
                        # não assume que seja a tabela certa; usa fallback abaixo
                    except Exception as e:
                        logger.debug(f"Erro contando <tr>: {e}")
                
                if not table:
                    # tentar mudar para frame padrão e procurar novamente
                    try:
                        self.driver.switch_to.default_content()
                        WebDriverWait(self.driver, 1).until(EC.frame_to_be_available_and_switch_to_it((By.NAME, 'ptifrmtgtframe')))
                        logger.info("✓ Switch para ptifrmtgtframe no fallback da extração")
                        for selector in table_selectors:
                            try:
                                table = self.driver.find_element(By.CSS_SELECTOR, selector)
                                if table:
                                    logger.info(f"✓ Tabela encontrada com selector (após switch): {selector}")
                                    break
                            except Exception:
                                continue
                    except Exception:
                        logger.debug("Não foi possível fazer switch/fallback para frame na extração")
                
                if table:
                    # Extrair linhas da tabela
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    logger.info(f"Encontradas {len(rows)} linhas na tabela")
                    
                    for row in rows[1:]:  # Pular cabeçalho
                        try:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) < 3:
                                continue
                            
                            # Extrair status (geralmente numa coluna específica)
                            row_text = row.text.lower()
                            
                            metrics['total_processes'] += 1
                            
                            # Identificar status
                            if any(word in row_text for word in ['error', 'erro', 'failed', 'falhou']):
                                metrics['failed'] += 1
                                
                                # Adicionar a lista de erros críticos
                                error_info = {
                                    'name': cells[0].text if len(cells) > 0 else 'Desconhecido',
                                    'message': cells[2].text if len(cells) > 2 else 'Erro',
                                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }
                                metrics['critical_errors'].append(error_info)
                                
                            elif any(word in row_text for word in ['success', 'sucesso', 'posted', 'complete']):
                                metrics['success'] += 1
                            elif any(word in row_text for word in ['running', 'processing', 'executando']):
                                metrics['running'] += 1
                                
                        except Exception as e:
                            logger.debug(f"Erro ao processar linha: {type(e).__name__} - {e}")
                            continue
                    
                    # Calcular taxa de sucesso
                    if metrics['total_processes'] > 0:
                        metrics['success_rate'] = round(
                            (metrics['success'] / metrics['total_processes']) * 100, 
                            2
                        )
                    
                    logger.info(f"✓ Métricas extraídas: {metrics['total_processes']} processos, "
                              f"{metrics['failed']} erros, {metrics['success_rate']}% sucesso")
                else:
                    # Salvar page source para depuração
                    try:
                        os.makedirs("storage/logs", exist_ok=True)
                        html_path = os.path.join("storage", "logs", "page_structure.html")
                        with open(html_path, "w", encoding="utf-8") as f:
                            f.write(self.driver.page_source)
                        logger.warning(f"⚠ Tabela de processos não encontrada — page_source salvo em {html_path}")
                        logger.warning(f"URL atual: {self.driver.current_url}")
                    except Exception as e:
                        logger.warning(f"⚠ Tabela de processos não encontrada e falha ao salvar page_source: {e}")
                    
                return metrics
                    
            except Exception as e:
                logger.warning(f"⚠ Erro ao extrair métricas da tabela: {type(e).__name__} - {e}\n{traceback.format_exc()}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair métricas: {e}\n{traceback.format_exc()}")
            return {
                'total_processes': 0,
                'running': 0,
                'failed': 0,
                'success': 0,
                'success_rate': 0.0,
                'critical_errors': []
            }
    
    def login_and_save_cookies(self) -> bool:
        """Faz login e salva cookies"""
        try:
            self._init_driver()
            
            logger.info(f"🔐 Fazendo login em {self.system_name}...")
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Preencher credenciais
            username = self.credentials.get('username')
            password = self.credentials.get('password')
            
            if not username or not password:
                logger.error("❌ Credenciais não configuradas")
                return False
            
            # Encontrar e preencher campos
            try:
                user_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "userid"))
                )
                user_field.clear()
                user_field.send_keys(username)
                
                pwd_field = self.driver.find_element(By.ID, "pwd")
                pwd_field.clear()
                pwd_field.send_keys(password)
                
                # Selecionar idioma
                try:
                    select = Select(self.driver.find_element(By.ID, "ptlangsel"))
                    select.select_by_value("POR")
                except Exception:
                    pass
                
                # Submeter login
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                submit_btn.click()
                
                time.sleep(5)
                
                # Verificar sucesso
                if "signon" in self.driver.current_url.lower():
                    logger.error("❌ Falha no login - ainda na página de login")
                    self.driver.save_screenshot("storage/logs/login_error.png")
                    return False
                
                # Salvar cookies
                cookies = self.driver.get_cookies()
                os.makedirs("config/credentials", exist_ok=True)
                
                with open(self.cookies_file, "wb") as f:
                    pickle.dump(cookies, f)
                
                logger.info(f"✓ Login OK! {len(cookies)} cookies salvos")
                return True
                
            except sel_ex.TimeoutException as e:
                logger.error("❌ Timeout ao procurar campos de login")
                return False
            
        except Exception as e:
            logger.error(f"❌ Erro no login: {e}\n{traceback.format_exc()}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None