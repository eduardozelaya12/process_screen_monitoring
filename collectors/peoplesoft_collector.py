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
        
        # ✅ NOVO: Carregar filtros do config
        self.filters = config.get('filters', {})
        
        # DEBUG: Logar filtros carregados
        logger.info(f"🔍 DEBUG __init__: Filtros carregados do config:")
        logger.info(f"   - Total de chaves: {len(self.filters)}")
        logger.info(f"   - Conteúdo: {self.filters}")
    
    def collect(self) -> Dict:
        """Coleta dados do PeopleSoft - Login direto toda vez"""
        try:
            logger.info(f"📸 Coletando dados: {self.system_name}")
            
            # Capturar screenshot e extrair dados (faz login internamente)
            screenshot_path, metrics = self._capture_and_extract()
            
            if not screenshot_path:
                return self._mark_error("Falha ao capturar dados")
            
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
        """Captura screenshot e extrai métricas - Faz login direto toda vez"""
        try:
            self._init_driver()
            
            # Fazer login direto (sem cookies)
            logger.info("🔐 Fazendo login...")
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Preencher credenciais
            try:
                username = self.credentials.get('username')
                password = self.credentials.get('password')
                
                if not username or not password:
                    logger.error("❌ Credenciais não configuradas")
                    return None, {}
                
                user_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "userid"))
                )
                user_field.clear()
                user_field.send_keys(username)
                
                pwd_field = self.driver.find_element(By.ID, "pwd")
                pwd_field.clear()
                pwd_field.send_keys(password)
                
                # Selecionar idioma (opcional)
                try:
                    select = Select(self.driver.find_element(By.ID, "ptlangsel"))
                    select.select_by_value("POR")
                except:
                    pass
                
                # Submeter login
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                submit_btn.click()
                time.sleep(5)
                
                # Verificar se login funcionou
                if "signon" in self.driver.current_url.lower():
                    logger.error("❌ Falha no login - ainda na página de login")
                    self.driver.save_screenshot("storage/logs/login_error.png")
                    return None, {}
                
                logger.info("✓ Login bem-sucedido")
                
            except Exception as e:
                logger.error(f"❌ Erro no login: {e}")
                return None, {}
            
            # Navegar para página de processos
            logger.info(f"Navegando para: {self.process_url}")
            self.driver.get(self.process_url)
            time.sleep(4)
            
            # Switch para iframe principal (seguindo padrão do teste)
            iframe_switched = False
            try:
                self.driver.switch_to.default_content()
                
                # Listar frames para debug
                frames = self.driver.find_elements(By.TAG_NAME, "iframe") + self.driver.find_elements(By.TAG_NAME, "frame")
                logger.debug(f"{len(frames)} frames encontrados")
                
                # Tentativa 1: Por NAME
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.frame_to_be_available_and_switch_to_it((By.NAME, "ptifrmtgtframe"))
                    )
                    logger.info("✓ Switch para iframe ptifrmtgtframe (por NAME)")
                    iframe_switched = True
                except Exception:
                    # Tentativa 2: Por ID
                    try:
                        self.driver.switch_to.default_content()
                        WebDriverWait(self.driver, 5).until(
                            EC.frame_to_be_available_and_switch_to_it((By.ID, "ptifrmtgtframe"))
                        )
                        logger.info("✓ Switch para iframe ptifrmtgtframe (por ID)")
                        iframe_switched = True
                    except Exception:
                        # Tentativa 3: Primeiro frame disponível
                        try:
                            self.driver.switch_to.default_content()
                            if frames:
                                self.driver.switch_to.frame(frames[0])
                                logger.info("✓ Switch para primeiro frame (por índice)")
                                iframe_switched = True
                        except Exception:
                            pass
                
                if not iframe_switched:
                    logger.warning("⚠ Não foi possível trocar para iframe, continuando sem switch")
                    
            except Exception as e:
                logger.debug(f"Erro ao processar frames: {e}")
            
            time.sleep(2)

            # --- ADICIONADO: continuar fluxo de extração (aplicar filtros, extrair métricas e salvar screenshot)
            try:
                # Aplicar filtros configurados (ou nenhum se não tiver)
                self._apply_filters()
                time.sleep(2)

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

    def _apply_filters(self):
        """Aplica filtros configurados antes de extrair métricas"""
        try:
            if not self.filters:
                logger.info("📋 Nenhum filtro configurado - processando todos os dados")
                return
            
            # Log detalhado dos filtros configurados
            logger.info("=" * 60)
            logger.info("📋 FILTROS CONFIGURADOS:")
            logger.info("=" * 60)
            
            if self.filters.get('user_id'):
                logger.info(f"  • User ID: {self.filters['user_id']}")
            if self.filters.get('process_name'):
                logger.info(f"  • Process Name: {self.filters['process_name']}")
            if self.filters.get('server'):
                logger.info(f"  • Server: {self.filters['server']}")
            if self.filters.get('run_status'):
                logger.info(f"  • Run Status: {self.filters['run_status']}")
            if self.filters.get('type'):
                logger.info(f"  • Type: {self.filters['type']}")
            if self.filters.get('dist_status'):
                logger.info(f"  • Distribution Status: {self.filters['dist_status']}")
            if self.filters.get('instance_from'):
                logger.info(f"  • Instance From: {self.filters['instance_from']}")
            if self.filters.get('instance_to'):
                logger.info(f"  • Instance To: {self.filters['instance_to']}")
            
            time_filter = self.filters.get('time_filter', {})
            if time_filter:
                logger.info(f"  • Time Filter:")
                if time_filter.get('type'):
                    type_name = "Last" if time_filter['type'] == "0" else "Date Range"
                    logger.info(f"    - Type: {type_name}")
                if time_filter.get('value'):
                    logger.info(f"    - Value: {time_filter['value']}")
                if time_filter.get('unit'):
                    unit_names = {"0": "All", "1": "Days", "2": "Hours", "3": "Minutes", "4": "Years"}
                    unit_name = unit_names.get(time_filter['unit'], time_filter['unit'])
                    logger.info(f"    - Unit: {unit_name}")
            
            logger.info("=" * 60)
            logger.info("🔍 Aplicando filtros...")
            
            # 1. User ID (via modal)
            if self.filters.get('user_id'):
                self._search_in_modal(
                    search_value=self.filters['user_id'],
                    modal_type="User ID",
                    prompt_id="PMN_FILTER_WRK_WS_OPRID$prompt",
                    search_field_id="PMN_OPRID_VW_OPRID"
                )
            
            # 2. Process Name (via modal)
            if self.filters.get('process_name'):
                self._search_in_modal(
                    search_value=self.filters['process_name'],
                    modal_type="Process Name",
                    prompt_id="PMN_FILTER_WRK_PRCSNAME$prompt",
                    search_field_id="PMN_PRCSNAME_VW_PRCSNAME"
                )
            
            # 3. Server
            if 'server' in self.filters:
                self._set_select_field("PMN_FILTER_WRK_SERVERNAME", self.filters['server'], "Server")
            
            # 4. Run Status
            if 'run_status' in self.filters:
                self._set_select_field("PMN_FILTER_WRK_RUNSTATUS", self.filters['run_status'], "Run Status")
            
            # 5. Type
            if 'type' in self.filters:
                self._set_select_field("PMN_FILTER_WRK_PRCSTYPE", self.filters['type'], "Type")
            
            # 6. Distribution Status
            if 'dist_status' in self.filters:
                self._set_select_field("PMN_FILTER_WRK_DISTSTATUS", self.filters['dist_status'], "Distribution Status")
            
            # 7. Instance Range
            if 'instance_from' in self.filters:
                self._set_text_field("PMN_DERIVED_PRCSINSTANCE", self.filters['instance_from'], "Instance From")
            if 'instance_to' in self.filters:
                self._set_text_field("PMN_DERIVED_TO_PRCSINSTANCE", self.filters['instance_to'], "Instance To")
            
            # 8. Time Filter
            time_filter = self.filters.get('time_filter', {})
            if time_filter:
                if 'type' in time_filter:
                    self._set_select_field("PMN_FILTER_WRK_PT_FILTERTYPE", time_filter['type'], "Time Filter Type")
                if 'value' in time_filter:
                    self._set_text_field("PMN_FILTER_WRK_PT_FILTERVALUE", time_filter['value'], "Time Filter Value")
                if 'unit' in time_filter:
                    self._set_select_field("PMN_FILTER_WRK_PT_FILTERUNIT", time_filter['unit'], "Time Filter Unit")
            
            # Clicar Refresh
            self._click_refresh()
            
            logger.info("✓ Filtros aplicados com sucesso")
            
        except Exception as e:
            logger.warning(f"⚠ Erro ao aplicar filtros: {e}")
    
    def _search_in_modal(self, search_value: str, modal_type: str, prompt_id: str, search_field_id: str):
        """Busca valor usando modal de lookup com detecção automática de iframe"""
        try:
            logger.info(f"Buscando {modal_type}: '{search_value}'")
            
            # 1. Clicar na lupa
            lupa = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, prompt_id))
            )
            self.driver.execute_script("arguments[0].click();", lupa)
            time.sleep(4)
            
            # 2. Detectar iframe do modal automaticamente
            self.driver.switch_to.default_content()
            modal_found = False
            
            # Tentar ptModFrame_0 até ptModFrame_9
            for i in range(10):
                try:
                    self.driver.switch_to.default_content()
                    WebDriverWait(self.driver, 1).until(
                        EC.frame_to_be_available_and_switch_to_it((By.ID, f"ptModFrame_{i}"))
                    )
                    logger.debug(f"Modal encontrado em ptModFrame_{i}")
                    modal_found = True
                    break
                except:
                    continue
            
            if not modal_found:
                logger.error("Iframe do modal não encontrado")
                return False
            
            time.sleep(1)
            
            # 3. Preencher campo de busca
            search_field = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, search_field_id))
            )
            search_field.clear()
            time.sleep(0.5)
            search_field.send_keys(search_value)
            time.sleep(2)
            
            # 4. Verificar se resultados apareceram
            try:
                self.driver.find_element(By.ID, "PTSRCHRESULTS")
                logger.debug("Resultados carregados automaticamente")
            except:
                # Tentar clicar Look Up
                try:
                    lookup_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.NAME, "#ICSearch"))
                    )
                    self.driver.execute_script("arguments[0].click();", lookup_btn)
                    time.sleep(3)
                except:
                    logger.debug("Botão Look Up não encontrado, continuando...")
            
            # 5. Selecionar resultado
            result_selectors = [
                (By.XPATH, f"//a[contains(text(), '{search_value.upper()}')]"),
                (By.LINK_TEXT, search_value.upper()),
                (By.ID, "SEARCH_RESULT1")
            ]
            
            result_found = False
            for by, selector in result_selectors:
                try:
                    result_link = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    self.driver.execute_script("arguments[0].click();", result_link)
                    logger.info(f"✓ {modal_type} '{search_value}' selecionado")
                    result_found = True
                    break
                except:
                    continue
            
            if not result_found:
                logger.warning(f"⚠ {modal_type} '{search_value}' não encontrado nos resultados")
            
            time.sleep(2)
            
            # 6. Voltar ao iframe principal
            self.driver.switch_to.default_content()
            WebDriverWait(self.driver, 5).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "ptifrmtgtframe"))
            )
            time.sleep(1)
            
            return result_found
            
        except Exception as e:
            logger.error(f"Erro ao buscar {modal_type}: {e}")
            try:
                self.driver.save_screenshot(f"storage/logs/erro_{modal_type.lower().replace(' ', '_')}_modal.png")
            except:
                pass
            return False
    
    def _set_select_field(self, field_id: str, value: Optional[str], field_name: str):
        """Define valor em dropdown ou limpa se None"""
        try:
            elem = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, field_id))
            )
            sel = Select(elem)
            
            if value is None:
                # Limpar selecionando primeira opção
                sel.select_by_index(0)
                logger.debug(f"{field_name} limpo")
            else:
                # Tentar selecionar por value
                try:
                    sel.select_by_value(value)
                    logger.debug(f"{field_name} = '{value}'")
                except:
                    # Fallback: tentar por texto visível
                    sel.select_by_visible_text(value)
                    logger.debug(f"{field_name} = '{value}' (por texto)")
            return True
        except Exception as e:
            logger.warning(f"Erro ao ajustar {field_name}: {e}")
            return False
    
    def _set_text_field(self, field_id: str, value: Optional[str], field_name: str):
        """Define valor em campo de texto ou limpa se None"""
        try:
            field = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, field_id))
            )
            field.clear()
            
            if value is not None:
                field.send_keys(value)
                logger.debug(f"{field_name} = '{value}'")
            else:
                logger.debug(f"{field_name} limpo")
            return True
        except Exception as e:
            logger.warning(f"Erro ao ajustar {field_name}: {e}")
            return False
    
    def _click_refresh(self):
        """Clica no botão Refresh com highlight visual"""
        try:
            logger.info("=" * 60)
            logger.info("🔄 INICIANDO CLIQUE NO REFRESH...")
            logger.info("=" * 60)
            
            # Screenshot ANTES do clique
            try:
                os.makedirs("storage/logs", exist_ok=True)
                self.driver.save_screenshot("storage/logs/antes_refresh.png")
                logger.info("📸 Screenshot ANTES do Refresh salvo")
            except:
                pass
            
            # Tentar múltiplos seletores
            selectors = [
                (By.ID, "REFRESH_BTN"),
                (By.XPATH, "//input[@value='Refresh']"),
                (By.XPATH, "//input[@type='button' and contains(@value, 'Refresh')]"),
                (By.XPATH, "//a[contains(@id, 'REFRESH')]"),
                (By.XPATH, "//button[contains(text(), 'Refresh')]")
            ]
            
            for idx, (by, selector) in enumerate(selectors, 1):
                try:
                    logger.info(f"   Tentativa {idx}: {by} = '{selector}'")
                    btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    
                    # HIGHLIGHT VISUAL - Borda vermelha piscante
                    logger.info("   ✨ Aplicando highlight no botão...")
                    original_style = btn.get_attribute('style')
                    self.driver.execute_script(
                        "arguments[0].setAttribute('style', 'border: 5px solid red; background: yellow;');",
                        btn
                    )
                    time.sleep(1)  # Pausa para ver o highlight
                    
                    # Screenshot COM HIGHLIGHT
                    try:
                        self.driver.save_screenshot("storage/logs/highlight_refresh.png")
                        logger.info("   📸 Screenshot COM HIGHLIGHT salvo")
                    except:
                        pass
                    
                    # Restaurar estilo e clicar
                    self.driver.execute_script(
                        f"arguments[0].setAttribute('style', '{original_style}');",
                        btn
                    )
                    
                    logger.info("   🖱️  CLICANDO no botão...")
                    self.driver.execute_script("arguments[0].click();", btn)
                    
                    logger.info("=" * 60)
                    logger.info("✅ REFRESH CLICADO COM SUCESSO!")
                    logger.info("⏳ Aguardando 5 segundos para página atualizar...")
                    logger.info("=" * 60)
                    time.sleep(5)
                    
                    # Screenshot DEPOIS do clique
                    try:
                        self.driver.save_screenshot("storage/logs/depois_refresh.png")
                        logger.info("📸 Screenshot DEPOIS do Refresh salvo")
                    except:
                        pass
                    
                    return True
                    
                except Exception as e:
                    logger.debug(f"   ❌ Falhou: {type(e).__name__}")
                    continue
            
            logger.warning("=" * 60)
            logger.warning("⚠️  BOTÃO REFRESH NÃO ENCONTRADO COM NENHUM SELETOR!")
            logger.warning("=" * 60)
            return False
            
        except Exception as e:
            logger.error(f"Erro ao clicar Refresh: {e}")
            return False

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
                    logger.debug("Tabela não encontrada com seletores CSS, tentando XPath...")
                    try:
                        possible = self.driver.find_elements(By.XPATH, "//table//tr")
                        logger.debug(f"Encontradas {len(possible)} <tr> em todo o documento (fallback)")
                    except Exception as e:
                        logger.debug(f"Erro contando <tr>: {e}")
                
                # Último recurso: verificar se já estamos no iframe correto
                if not table:
                    logger.info("Tabela ainda não encontrada, verificando contexto de frame...")
                    try:
                        # Volta para default e tenta novamente
                        self.driver.switch_to.default_content()
                        WebDriverWait(self.driver, 2).until(
                            EC.frame_to_be_available_and_switch_to_it((By.NAME, 'ptifrmtgtframe'))
                        )
                        logger.info("✓ Realizou switch para ptifrmtgtframe no fallback")
                        
                        # Tenta seletores novamente após switch
                        for selector in table_selectors:
                            try:
                                table = self.driver.find_element(By.CSS_SELECTOR, selector)
                                if table:
                                    logger.info(f"✓ Tabela encontrada após switch: {selector}")
                                    break
                            except Exception:
                                continue
                    except Exception as e:
                        logger.debug(f"Não foi possível fazer switch para frame: {type(e).__name__}")
                
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