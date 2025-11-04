import sys
import logging
import json
from selenium.webdriver.common.by import By   # <-- Adicione aqui!

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from collectors.peoplesoft_collector import PeopleSoftCollector

def test_collector():
    """Testa o coletor PeopleSoft"""
    print("\n" + "="*60)
    print("TESTE DO COLETOR PEOPLESOFT")
    print("="*60 + "\n")
    
    # Carregar configuração
    with open('config/systems_config.json', 'r') as f:
        config = json.load(f)
    
    peoplesoft_config = config['peoplesoft']
    
    # Criar coletor
    collector = PeopleSoftCollector(peoplesoft_config)
    
    # Teste 1: Conexão
    print("Teste 1: Testando conexão...")
    if collector.test_connection():
        print("✓ Conexão OK\n")
    else:
        print("❌ Falha na conexão\n")
        return
    
    # Teste 2: Login
    print("Teste 2: Fazendo login e salvando cookies...")
    if collector.login_and_save_cookies():
        print("✓ Login OK\n")
    else:
        print("❌ Falha no login\n")
        return
    
    # Teste 3: Coleta
    print("Teste 3: Coletando dados...")
    result = collector.collect()
    
    if result['status'] == 'success':
        print("✓ Coleta bem-sucedida!")
        print(f"\nDados coletados:")
        print(f"  Screenshot: {result['data'].get('screenshot_path')}")
        print(f"  Métricas: {result['data'].get('metrics')}")
    else:
        print(f"❌ Erro na coleta: {result.get('error')}")
    
    print("\n" + "="*60)

def test_login_gui():
    from collectors.peoplesoft_collector import PeopleSoftCollector
    import json
    import time
    from selenium.webdriver.common.by import By  # <-- ADICIONE ESSA LINHA

    with open('config/systems_config.json', 'r') as f:
        config = json.load(f)
    peoplesoft_config = config['peoplesoft']
    collector = PeopleSoftCollector(peoplesoft_config)

    collector._init_driver()
    driver = collector.driver

    try:
        print(">> Acessando base_url para login manual...")
        driver.get(collector.base_url)
        time.sleep(3)

        # >>>>> CORRIGIDO ABAIXO
        driver.find_element(By.ID, "userid").send_keys(peoplesoft_config["credentials"]["username"])
        driver.find_element(By.ID, "pwd").send_keys(peoplesoft_config["credentials"]["password"])

        # Se o idioma não for obrigatório, pode omitir
        try:
            lang = driver.find_element(By.ID, "ptlangsel")
            lang.send_keys("Portuguese (Brazil)")
        except Exception:
            pass

        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        time.sleep(4)

        print(">> Título pós-login:", driver.title)
        print(">> URL pós-login:", driver.current_url)
        driver.save_screenshot("storage/logs/login_step.png")

        # Verifica se ainda está na tela de login
        if "login" in driver.title.lower() or "signon" in driver.current_url.lower():
            print("[ERRO] Continua na tela de login. Login falhou ou faltam etapas!")
        else:
            print("[OK] Login funcionou.")

    finally:
        driver.quit()

def test_navegacao_monitor():
    from collectors.peoplesoft_collector import PeopleSoftCollector
    import json
    import time
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC

    with open('config/systems_config.json', 'r') as f:
        config = json.load(f)
    peoplesoft_config = config['peoplesoft']
    collector = PeopleSoftCollector(peoplesoft_config)
    collector._init_driver()
    driver = collector.driver

    try:
        # Login manual (pode reusar a função acima)
        driver.get(collector.base_url)
        time.sleep(3)
        driver.find_element(By.ID, "userid").send_keys(peoplesoft_config["credentials"]["username"])
        driver.find_element(By.ID, "pwd").send_keys(peoplesoft_config["credentials"]["password"])
        driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
        time.sleep(4)

        # Navegar para monitor
        print(">> Navegando para monitor de processos...")
        driver.get(collector.process_url)
        time.sleep(4)

        # Tentar entrar no iframe do conteúdo principal
        iframe_switched = False
        try:
            driver.switch_to.default_content()
            
            # Listar todos os iframes disponíveis para debug
            iframes = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
            print(f">> {len(iframes)} frames encontrados na página")
            for idx, frame in enumerate(iframes):
                frame_id = frame.get_attribute('id') or '(sem id)'
                frame_name = frame.get_attribute('name') or '(sem name)'
                print(f"   Frame {idx}: id='{frame_id}', name='{frame_name}'")
            
            # Tentar múltiplas formas de acessar o iframe
            try:
                # Tentativa 1: Por NAME
                WebDriverWait(driver, 5).until(
                    EC.frame_to_be_available_and_switch_to_it((By.NAME, "ptifrmtgtframe"))
                )
                print(">> ✓ Switch para iframe ptifrmtgtframe OK (por NAME)")
                iframe_switched = True
            except Exception as e1:
                print(f">> Tentativa por NAME falhou: {type(e1).__name__}")
                try:
                    # Tentativa 2: Por ID
                    driver.switch_to.default_content()
                    WebDriverWait(driver, 5).until(
                        EC.frame_to_be_available_and_switch_to_it((By.ID, "ptifrmtgtframe"))
                    )
                    print(">> ✓ Switch para iframe ptifrmtgtframe OK (por ID)")
                    iframe_switched = True
                except Exception as e2:
                    print(f">> Tentativa por ID falhou: {type(e2).__name__}")
                    try:
                        # Tentativa 3: Por índice (geralmente é o primeiro ou único)
                        driver.switch_to.default_content()
                        if iframes:
                            driver.switch_to.frame(iframes[0])
                            print(">> ✓ Switch para primeiro iframe OK (por índice)")
                            iframe_switched = True
                        else:
                            print(">> Nenhum iframe encontrado")
                    except Exception as e3:
                        print(f">> Tentativa por índice falhou: {type(e3).__name__}")
        
        except Exception as e:
            print(f">> Erro ao processar iframes: {e}")
        
        if not iframe_switched:
            print(">> ⚠️ AVISO: Não foi possível trocar para iframe! Elementos podem não ser encontrados.")
        
        # Aguardar um pouco mais após switch
        time.sleep(2)

        # Perguntar filtros ao usuário
        print("\n" + "="*60)
        print("FILTROS DISPONÍVEIS (pressione Enter para pular)")
        print("="*60)
        
        # User ID (com busca em modal)
        user_id_val = input("\n1. User ID (ex.: MBENITEZ, AJPEOPLE...): ").strip()
        # Se vazio, definir como None para limpar filtro
        user_id_val = user_id_val if user_id_val else None
        
        # Process Name (com busca em modal)
        process_name_val = input("\n2. Process Name (ex.: AJ_LDEXP, GL_LEDGER...): ").strip()
        process_name_val = process_name_val if process_name_val else None
        
        # Server
        server_val = input("\n3. Server (ex.: PSUNX, AJNODE4B, AJNODE4C...): ").strip()
        server_val = server_val if server_val else None
        
        # Run Status
        print("\n4. Run Status:")
        print("   1=Cancel, 3=Error, 7=Processing, 8=Cancelled")
        print("   9=Success, 10=No Success, 17=Warning, 18=Blocked")
        run_status_val = input("   Valor: ").strip()
        run_status_val = run_status_val if run_status_val else None
        
        # Type
        print("\n5. Type:")
        print("   Application Engine, PSJob, SQR Report, Crystal...")
        type_val = input("   Valor: ").strip()
        type_val = type_val if type_val else None
        
        # Distribution Status
        print("\n6. Distribution Status:")
        print("   2=Processing, 3=Generated, 4=Not Posted, 5=Posted, 9=Pending")
        dist_status_val = input("   Valor: ").strip()
        dist_status_val = dist_status_val if dist_status_val else None
        
        # Instance Range
        instance_from = input("\n7. Instance From (número, ex.: 7997100): ").strip()
        instance_from = instance_from if instance_from else None
        instance_to = input("   Instance To (número, ex.: 7997200): ").strip()
        instance_to = instance_to if instance_to else None
        
        # Time Filter
        print("\n8. Time Filter:")
        print("   Type: 0=Last (padrão), 1=Date Range")
        time_filter_type = input("   Type: ").strip()
        time_filter_type = time_filter_type if time_filter_type else None
        time_value = input("   Value (número, ex.: 70): ").strip()
        time_value = time_value if time_value else None
        print("   Unit: 0=All, 1=Days, 2=Hours, 3=Minutes, 4=Years")
        time_unit = input("   Unit: ").strip()
        time_unit = time_unit if time_unit else None
        
        print("\n" + "="*60)

        # Aplicar filtros se fornecidos
        def clear_select_by_id(select_id: str):
            """Limpa/reseta um dropdown selecionando a primeira opção (vazia)"""
            try:
                elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, select_id))
                )
                sel = Select(elem)
                # Selecionar primeira opção (geralmente vazia)
                sel.select_by_index(0)
                print(f"   ✓ {select_id} limpo (primeira opção selecionada)")
                return True
            except Exception as e:
                print(f"   ⚠️ Não foi possível limpar {select_id}: {type(e).__name__}")
                return False
        
        def clear_text_field(field_id: str):
            """Limpa um campo de texto"""
            try:
                field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, field_id))
                )
                field.clear()
                print(f"   ✓ {field_id} limpo")
                return True
            except Exception as e:
                print(f"   ⚠️ Não foi possível limpar {field_id}: {type(e).__name__}")
                return False
        
        def set_select_by_id(select_id: str, value_or_text: str):
            """Define valor em dropdown ou limpa se None"""
            # Se valor é None, limpar campo
            if value_or_text is None:
                return clear_select_by_id(select_id)
            
            try:
                print(f"   Procurando elemento: {select_id}")
                elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, select_id))
                )
                print(f"   ✓ Elemento {select_id} encontrado")
                sel = Select(elem)
                
                # Listar opções disponíveis para debug
                options = [opt.get_attribute('value') for opt in sel.options]
                print(f"   Opções disponíveis: {options[:5]}...")  # Mostrar primeiras 5
                
                # Primeiro tenta por value; se falhar, tenta por texto visível
                try:
                    sel.select_by_value(value_or_text)
                    print(f"   ✓ {select_id} ajustado para '{value_or_text}' (por value)")
                    return True
                except Exception as e1:
                    print(f"   Tentativa por value falhou: {type(e1).__name__}")
                    try:
                        sel.select_by_visible_text(value_or_text)
                        print(f"   ✓ {select_id} ajustado para '{value_or_text}' (por texto)")
                        return True
                    except Exception as e2:
                        print(f"   Tentativa por texto falhou: {type(e2).__name__}")
                        return False
            except Exception as e:
                print(f"   ❌ ERRO ao ajustar {select_id}: {type(e).__name__}")
                print(f"      Detalhes: {str(e)[:100]}")
                return False
        
        def set_text_field(field_id: str, value: str, field_name: str):
            """Define valor em campo de texto ou limpa se None"""
            # Se valor é None, limpar campo
            if value is None:
                print(f"   Limpando campo {field_name}...")
                return clear_text_field(field_id)
            
            try:
                print(f"   Procurando campo de texto: {field_id}")
                field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, field_id))
                )
                field.clear()
                field.send_keys(value)
                print(f"   ✓ {field_name} ajustado para '{value}'")
                return True
            except Exception as e:
                print(f"   ❌ ERRO ao ajustar {field_name}: {type(e).__name__}")
                return False
        
        def search_in_modal(search_value: str, modal_type: str, modal_frame: str, 
                            prompt_id: str, search_field_id: str, result_contains: str):
            """
            Função genérica para buscar em modais do PeopleSoft
            
            Modal Frames:
            - User ID modal: ptModFrame_1
            - Process Name modal: ptModFrame_2
            - Outros modais: ptModFrame_0, ptModFrame_3, etc.
            """
            try:
                print(f"\n>> Buscando {modal_type} '{search_value}' via modal...")
                
                # 1. Clicar na lupa para abrir modal
                print(f"   1. Clicando na lupa de {modal_type}...")
                try:
                    lupa = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, prompt_id))
                    )
                    driver.execute_script("arguments[0].click();", lupa)
                    print("   ✓ Lupa clicada, aguardando modal abrir...")
                    time.sleep(4)
                except Exception as e:
                    print(f"   ❌ Erro ao clicar na lupa: {type(e).__name__}")
                    return False
                
                # 1.5. Fazer switch para o iframe do modal (detectar automaticamente)
                print(f"   1.5. Detectando iframe do modal...")
                try:
                    driver.switch_to.default_content()
                    
                    # Abordagem 1: Procurar por qualquer ptModFrame_* disponível
                    modal_found = False
                    
                    # Tentar iframe específico primeiro (se fornecido)
                    if modal_frame:
                        try:
                            WebDriverWait(driver, 3).until(
                                EC.frame_to_be_available_and_switch_to_it((By.ID, modal_frame))
                            )
                            print(f"   ✓ Switch para iframe '{modal_frame}' OK")
                            modal_found = True
                        except:
                            pass
                    
                    # Se não encontrou, procurar por qualquer ptModFrame_X
                    if not modal_found:
                        print(f"   → Procurando por qualquer iframe ptModFrame_*...")
                        
                        # Tentar ptModFrame_0 até ptModFrame_9
                        for i in range(10):
                            frame_name = f"ptModFrame_{i}"
                            try:
                                driver.switch_to.default_content()
                                WebDriverWait(driver, 1).until(
                                    EC.frame_to_be_available_and_switch_to_it((By.ID, frame_name))
                                )
                                print(f"   ✓ Modal encontrado em '{frame_name}'!")
                                modal_found = True
                                break
                            except:
                                continue
                    
                    # Abordagem 2: Procurar por iframe que contenha "ptModFrame" usando XPath
                    if not modal_found:
                        print(f"   → Tentando XPath para encontrar modal...")
                        try:
                            driver.switch_to.default_content()
                            # Procurar qualquer iframe com id que comece com ptModFrame
                            modal_frames = driver.find_elements(By.XPATH, "//iframe[starts-with(@id, 'ptModFrame')]")
                            
                            if modal_frames:
                                # Tentar o último iframe encontrado (mais recente)
                                frame_id = modal_frames[-1].get_attribute('id')
                                print(f"   → Encontrado iframe: {frame_id}")
                                
                                driver.switch_to.default_content()
                                WebDriverWait(driver, 3).until(
                                    EC.frame_to_be_available_and_switch_to_it((By.ID, frame_id))
                                )
                                print(f"   ✓ Switch para '{frame_id}' OK (via XPath)")
                                modal_found = True
                        except Exception as e:
                            print(f"   ⚠️ XPath falhou: {type(e).__name__}")
                    
                    if not modal_found:
                        print("   ❌ Não foi possível encontrar iframe do modal")
                        return False
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"   ❌ Erro ao fazer switch: {type(e).__name__}")
                    return False
                
                # 2. Preencher campo de busca
                print("   2. Preenchendo campo de busca...")
                try:
                    search_field = None
                    selectors = [
                        (By.ID, search_field_id),
                        (By.XPATH, f"//input[contains(@id, '{search_field_id.split('_')[-1]}')]"),
                        (By.XPATH, "//input[@type='text' and contains(@class, 'PSEDITBOX')]")
                    ]
                    
                    for by, selector in selectors:
                        try:
                            search_field = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((by, selector))
                            )
                            print(f"   ✓ Campo encontrado com: {selector}")
                            break
                        except:
                            continue
                    
                    if not search_field:
                        print("   ❌ Campo de busca não encontrado")
                        return False
                    
                    search_field.clear()
                    time.sleep(0.5)
                    search_field.send_keys(search_value)
                    print(f"   ✓ Digitado '{search_value}' no campo")
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"   ❌ Erro ao preencher campo: {type(e).__name__}")
                    return False
                
                # 3. Verificar se resultados já apareceram
                print("   3. Verificando resultados...")
                try:
                    time.sleep(2)
                    try:
                        results_table = driver.find_element(By.ID, "PTSRCHRESULTS")
                        print("   ✓ Resultados já carregados (busca automática)")
                    except:
                        print("   → Resultados não apareceram, clicando em Look Up...")
                        button_selectors = [
                            (By.NAME, "#ICSearch"),
                            (By.XPATH, "//input[@name='#ICSearch']"),
                            (By.XPATH, "//input[@value='Look Up' and @type='button']"),
                            (By.CSS_SELECTOR, "input.PSPUSHBUTTONTBLOOKUP[value='Look Up']")
                        ]
                        
                        lookup_btn = None
                        for by, selector in button_selectors:
                            try:
                                lookup_btn = WebDriverWait(driver, 3).until(
                                    EC.element_to_be_clickable((by, selector))
                                )
                                break
                            except:
                                continue
                        
                        if lookup_btn:
                            driver.execute_script("arguments[0].click();", lookup_btn)
                            print("   ✓ Botão Look Up clicado")
                            time.sleep(3)
                        else:
                            print("   ⚠️ Botão não encontrado, continuando...")
                    
                except Exception as e:
                    print(f"   ⚠️ Aviso: {type(e).__name__}")
                
                # 4. Procurar e clicar no resultado
                print("   4. Procurando resultado...")
                try:
                    result_link = None
                    result_selectors = [
                        (By.XPATH, f"//a[contains(text(), '{result_contains.upper()}')]"),
                        (By.XPATH, f"//td[contains(text(), '{result_contains.upper()}')]/a"),
                        (By.LINK_TEXT, result_contains.upper()),
                        (By.ID, "SEARCH_RESULT1")
                    ]
                    
                    for by, selector in result_selectors:
                        try:
                            result_link = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((by, selector))
                            )
                            print(f"   ✓ Resultado encontrado")
                            break
                        except:
                            continue
                    
                    if result_link:
                        driver.execute_script("arguments[0].click();", result_link)
                        print(f"   ✓ {modal_type} '{search_value}' selecionado!")
                        time.sleep(2)
                        
                        # 5. Voltar ao iframe principal
                        print("   5. Voltando ao iframe principal...")
                        try:
                            driver.switch_to.default_content()
                            WebDriverWait(driver, 5).until(
                                EC.frame_to_be_available_and_switch_to_it((By.ID, "ptifrmtgtframe"))
                            )
                            print("   ✓ De volta ao iframe ptifrmtgtframe")
                        except:
                            print("   ⚠️ Aviso ao voltar ao iframe principal")
                        
                        time.sleep(1)
                        return True
                    else:
                        print(f"   ⚠️ {modal_type} '{search_value}' não encontrado")
                        return False
                        
                except Exception as e:
                    print(f"   ❌ Erro ao processar resultado: {type(e).__name__}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ ERRO GERAL: {type(e).__name__}")
                try:
                    driver.save_screenshot(f"storage/logs/erro_{modal_type.lower().replace(' ', '_')}_modal.png")
                    print(f"   📸 Screenshot salvo")
                except:
                    pass
                return False
        
        def search_user_id_modal(user_id: str):
            """
            Busca User ID usando o modal de lookup
            Detecta automaticamente qual iframe modal foi aberto (ptModFrame_0, 1, 2, etc.)
            """
            return search_in_modal(
                search_value=user_id,
                modal_type="User ID",
                modal_frame=None,  # Detecta automaticamente!
                prompt_id="PMN_FILTER_WRK_WS_OPRID$prompt",
                search_field_id="PMN_OPRID_VW_OPRID",
                result_contains=user_id
            )
        
        def search_process_name_modal(process_name: str):
            """
            Busca Process Name usando o modal de lookup
            Detecta automaticamente qual iframe modal foi aberto (ptModFrame_0, 1, 2, etc.)
            """
            return search_in_modal(
                search_value=process_name,
                modal_type="Process Name",
                modal_frame=None,  # Detecta automaticamente!
                prompt_id="PMN_FILTER_WRK_PRCSNAME$prompt",
                search_field_id="PMN_PRCSNAME_VW_PRCSNAME",
                result_contains=process_name
            )
        
        def search_user_id_modal_OLD(user_id: str):
            """FUNÇÃO ANTIGA - Mantida para referência"""
            try:
                print(f"\n>> Buscando User ID '{user_id}' via modal...")
                
                # 1. Clicar na lupa para abrir modal
                print("   1. Clicando na lupa de User ID...")
                try:
                    lupa = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "PMN_FILTER_WRK_WS_OPRID$prompt"))
                    )
                    driver.execute_script("arguments[0].click();", lupa)
                    print("   ✓ Lupa clicada, aguardando modal abrir...")
                    time.sleep(4)  # Aguardar modal abrir completamente
                except Exception as e:
                    print(f"   ❌ Erro ao clicar na lupa: {type(e).__name__}")
                    return False
                
                # 1.5. Fazer switch para o iframe do modal
                print("   1.5. Fazendo switch para iframe do modal...")
                try:
                    # Voltar ao contexto principal primeiro
                    driver.switch_to.default_content()
                    
                    # Tentar múltiplos nomes de iframe do modal
                    modal_frame_names = [
                        "ptModFrame_1",
                        "ptModFrame_0",
                        "ptModFrame"
                    ]
                    
                    switched = False
                    for frame_name in modal_frame_names:
                        try:
                            WebDriverWait(driver, 5).until(
                                EC.frame_to_be_available_and_switch_to_it((By.ID, frame_name))
                            )
                            print(f"   ✓ Switch para iframe '{frame_name}' OK")
                            switched = True
                            break
                        except:
                            try:
                                WebDriverWait(driver, 2).until(
                                    EC.frame_to_be_available_and_switch_to_it((By.NAME, frame_name))
                                )
                                print(f"   ✓ Switch para iframe '{frame_name}' OK (por NAME)")
                                switched = True
                                break
                            except:
                                continue
                    
                    if not switched:
                        print("   ⚠️ Não foi possível fazer switch para iframe do modal")
                        print("   → Tentando continuar mesmo assim...")
                    
                    time.sleep(1)  # Aguardar iframe carregar
                    
                except Exception as e:
                    print(f"   ⚠️ Aviso ao fazer switch: {type(e).__name__}")
                
                # 2. Preencher campo de busca no modal
                print("   2. Preenchendo campo de busca...")
                try:
                    # Tentar múltiplos seletores para o campo
                    search_field = None
                    selectors = [
                        (By.ID, "PMN_OPRID_VW_OPRID"),
                        (By.XPATH, "//input[contains(@id, 'OPRID')]"),
                        (By.XPATH, "//input[@type='text' and contains(@class, 'PSEDITBOX')]")
                    ]
                    
                    for by, selector in selectors:
                        try:
                            search_field = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((by, selector))
                            )
                            print(f"   ✓ Campo encontrado com: {selector}")
                            break
                        except:
                            continue
                    
                    if not search_field:
                        print("   ❌ Campo de busca não encontrado")
                        return False
                    
                    search_field.clear()
                    time.sleep(0.5)
                    search_field.send_keys(user_id)
                    print(f"   ✓ Digitado '{user_id}' no campo")
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"   ❌ Erro ao preencher campo: {type(e).__name__}")
                    return False
                
                # 3. Verificar se resultados já apareceram ou clicar Look Up
                print("   3. Verificando resultados...")
                try:
                    # Primeiro verificar se resultados já apareceram
                    time.sleep(2)  # Aguardar um pouco
                    try:
                        # Procurar tabela de resultados
                        results_table = driver.find_element(By.ID, "PTSRCHRESULTS")
                        print("   ✓ Resultados já carregados (busca automática)")
                    except:
                        # Resultados não apareceram, precisa clicar no botão
                        print("   → Resultados não apareceram, clicando em Look Up...")
                        lookup_btn = None
                        button_selectors = [
                            (By.NAME, "#ICSearch"),  # Tentar por NAME primeiro
                            (By.XPATH, "//input[@name='#ICSearch']"),
                            (By.XPATH, "//input[@id='#ICSearch']"),  # ID tem # no nome
                            (By.XPATH, "//input[@value='Look Up' and @type='button']"),
                            (By.XPATH, "//input[contains(@class, 'PSPUSHBUTTONTBLOOKUP') and @value='Look Up']"),
                            (By.CSS_SELECTOR, "input.PSPUSHBUTTONTBLOOKUP[value='Look Up']")
                        ]
                        
                        for by, selector in button_selectors:
                            try:
                                lookup_btn = WebDriverWait(driver, 3).until(
                                    EC.element_to_be_clickable((by, selector))
                                )
                                print(f"   ✓ Botão encontrado com: {selector}")
                                break
                            except:
                                continue
                        
                        if lookup_btn:
                            driver.execute_script("arguments[0].click();", lookup_btn)
                            print("   ✓ Botão Look Up clicado, aguardando resultados...")
                            time.sleep(3)  # Aguardar resultados carregarem
                        else:
                            print("   ⚠️ Botão Look Up não encontrado, mas continuando...")
                            # Não retorna False, tenta encontrar resultado mesmo assim
                    
                except Exception as e:
                    print(f"   ⚠️ Aviso ao processar Look Up: {type(e).__name__}")
                    # Não retorna False, continua tentando encontrar resultado
                
                # 4. Tentar clicar no resultado (se existir)
                print("   4. Procurando resultado...")
                try:
                    # Tentar múltiplos seletores para o resultado
                    result_link = None
                    result_selectors = [
                        (By.XPATH, f"//a[contains(@class, 'PSSRCHRESULTS') and contains(text(), '{user_id.upper()}')]"),
                        (By.XPATH, f"//a[contains(text(), '{user_id.upper()}')]"),
                        (By.XPATH, f"//td[contains(text(), '{user_id.upper()}')]/a"),
                        (By.LINK_TEXT, user_id.upper()),
                        (By.ID, "SEARCH_RESULT1")  # Primeiro resultado
                    ]
                    
                    for by, selector in result_selectors:
                        try:
                            result_link = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((by, selector))
                            )
                            print(f"   ✓ Resultado encontrado com: {selector}")
                            break
                        except:
                            continue
                    
                    if result_link:
                        driver.execute_script("arguments[0].click();", result_link)
                        print(f"   ✓ User ID '{user_id}' selecionado!")
                        time.sleep(2)  # Aguardar modal fechar
                        
                        # Voltar ao iframe principal após fechar modal
                        print("   5. Voltando ao iframe principal...")
                        try:
                            driver.switch_to.default_content()
                            WebDriverWait(driver, 5).until(
                                EC.frame_to_be_available_and_switch_to_it((By.ID, "ptifrmtgtframe"))
                            )
                            print("   ✓ De volta ao iframe ptifrmtgtframe")
                        except:
                            try:
                                driver.switch_to.default_content()
                                WebDriverWait(driver, 5).until(
                                    EC.frame_to_be_available_and_switch_to_it((By.NAME, "TargetContent"))
                                )
                                print("   ✓ De volta ao iframe TargetContent")
                            except Exception as e:
                                print(f"   ⚠️ Aviso ao voltar ao iframe principal: {type(e).__name__}")
                        
                        time.sleep(1)
                        return True
                    else:
                        print(f"   ⚠️ User ID '{user_id}' não encontrado nos resultados")
                        # Tentar fechar modal
                        try:
                            cancel_selectors = [
                                (By.XPATH, "//input[@value='Cancel']"),
                                (By.ID, "pt_modals_close"),
                                (By.XPATH, "//button[contains(text(), 'Cancel')]")
                            ]
                            for by, selector in cancel_selectors:
                                try:
                                    cancel_btn = driver.find_element(by, selector)
                                    driver.execute_script("arguments[0].click();", cancel_btn)
                                    time.sleep(1)
                                    break
                                except:
                                    continue
                        except:
                            pass
                        return False
                        
                except Exception as e:
                    print(f"   ❌ Erro ao processar resultado: {type(e).__name__}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ ERRO GERAL ao buscar User ID: {type(e).__name__}")
                print(f"      Detalhes: {str(e)[:150]}")
                # Tentar salvar screenshot do erro
                try:
                    driver.save_screenshot("storage/logs/erro_user_id_modal.png")
                    print("   📸 Screenshot do erro salvo em: storage/logs/erro_user_id_modal.png")
                except:
                    pass
                return False
        
        # APLICAR FILTROS
        print("\n" + "="*60)
        print("APLICANDO FILTROS...")
        print("="*60)
        
        # 1. User ID (via modal)
        if user_id_val:
            search_user_id_modal(user_id_val)
        
        # 2. Process Name (via modal)
        if process_name_val:
            search_process_name_modal(process_name_val)
        
        # 3. Server (sempre aplica, limpa se None)
        print("\n>> Aplicando filtro Server...")
        if server_val is None:
            print("   → Limpando filtro...")
        set_select_by_id("PMN_FILTER_WRK_SERVERNAME", server_val)
        
        # 4. Run Status (sempre aplica, limpa se None)
        print("\n>> Aplicando filtro Run Status...")
        if run_status_val is None:
            print("   → Limpando filtro...")
        set_select_by_id("PMN_FILTER_WRK_RUNSTATUS", run_status_val)
        
        # 5. Type (sempre aplica, limpa se None)
        print("\n>> Aplicando filtro Type...")
        if type_val is None:
            print("   → Limpando filtro...")
        set_select_by_id("PMN_FILTER_WRK_PRCSTYPE", type_val)
        
        # 6. Distribution Status (sempre aplica, limpa se None)
        print("\n>> Aplicando filtro Distribution Status...")
        if dist_status_val is None:
            print("   → Limpando filtro...")
        set_select_by_id("PMN_FILTER_WRK_DISTSTATUS", dist_status_val)
        
        # 7. Instance From/To (sempre aplica, limpa se None)
        print("\n>> Aplicando filtro Instance From...")
        if instance_from is None:
            print("   → Limpando filtro...")
        set_text_field("PMN_DERIVED_PRCSINSTANCE", instance_from, "Instance From")
        
        print("\n>> Aplicando filtro Instance To...")
        if instance_to is None:
            print("   → Limpando filtro...")
        set_text_field("PMN_DERIVED_TO_PRCSINSTANCE", instance_to, "Instance To")
        
        # 8. Time Filter Type (sempre aplica, limpa se None)
        print("\n>> Aplicando Time Filter Type...")
        if time_filter_type is None:
            print("   → Limpando filtro...")
        set_select_by_id("PMN_FILTER_WRK_PT_FILTERTYPE", time_filter_type)
        
        # 9. Time Filter Value (sempre aplica, limpa se None)
        print("\n>> Aplicando Time Filter Value...")
        if time_value is None:
            print("   → Limpando filtro...")
        set_text_field("PMN_FILTER_WRK_PT_FILTERVALUE", time_value, "Time Filter Value")
        
        # 10. Time Filter Unit (sempre aplica, limpa se None)
        print("\n>> Aplicando Time Filter Unit...")
        if time_unit is None:
            print("   → Limpando filtro...")
        set_select_by_id("PMN_FILTER_WRK_PT_FILTERUNIT", time_unit)

        # Clicar Refresh
        print("\n>> Tentando clicar no botão Refresh...")
        refresh_clicked = False
        try:
            # Tentativa 1: Por ID
            try:
                refresh_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "REFRESH_BTN"))
                )
                driver.execute_script("arguments[0].click();", refresh_btn)
                print("   ✓ Refresh clicado (por ID)")
                refresh_clicked = True
            except Exception as e1:
                print(f"   Tentativa por ID falhou: {type(e1).__name__}")
                
                # Tentativa 2: Por texto do botão
                try:
                    refresh_btn = driver.find_element(By.XPATH, "//input[@value='Refresh' or @value='Atualizar']")
                    driver.execute_script("arguments[0].click();", refresh_btn)
                    print("   ✓ Refresh clicado (por XPath texto)")
                    refresh_clicked = True
                except Exception as e2:
                    print(f"   Tentativa por XPath falhou: {type(e2).__name__}")
                    
                    # Tentativa 3: Procurar qualquer botão com "refresh" no ID
                    try:
                        refresh_btn = driver.find_element(By.XPATH, "//*[contains(@id, 'REFRESH') or contains(@id, 'refresh')]")
                        driver.execute_script("arguments[0].click();", refresh_btn)
                        print("   ✓ Refresh clicado (por contains)")
                        refresh_clicked = True
                    except Exception as e3:
                        print(f"   Tentativa por contains falhou: {type(e3).__name__}")
            
            if refresh_clicked:
                print(">> Aguardando atualização da grid...")
                time.sleep(4)
            else:
                print(">> ⚠️ Não foi possível clicar em Refresh - continuando mesmo assim")
                
        except Exception as e:
            print(f">> Erro ao processar botão Refresh: {e}")

        print(">> Título após navegação:", driver.title)
        print(">> URL após navegação:", driver.current_url)
        driver.save_screenshot("storage/logs/navegacao_monitor.png")

        with open("storage/logs/dump_monitor.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        if "login" in driver.title.lower() or "signon" in driver.current_url.lower():
            print("[ERRO] Caiu na tela de login ao tentar abrir o Monitor.")
        else:
            print("[OK] Tela do monitor potencialmente acessível.")

    finally:
        driver.quit()

def test_cookies_acessam_monitor():
    from collectors.peoplesoft_collector import PeopleSoftCollector
    import json
    import pickle
    import time

    with open('config/systems_config.json', 'r') as f:
        config = json.load(f)
    peoplesoft_config = config['peoplesoft']
    collector = PeopleSoftCollector(peoplesoft_config)
    collector._init_driver()
    driver = collector.driver

    try:
        driver.get(collector.base_url)
        time.sleep(2)
        with open(collector.cookies_file, "rb") as f:
            cookies = pickle.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()
        time.sleep(2)

        # Navega para monitor directo usando os cookies
        print(">> Acessando monitor de processos só com cookies.")
        driver.get(collector.process_url)
        time.sleep(4)

        print(">> Título:", driver.title)
        print(">> URL:", driver.current_url)
        driver.save_screenshot("storage/logs/cookies_aplicados.png")
        with open("storage/logs/cookies_test_monitor.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        # Após o driver.get(process_url) e time.sleep(4)

        title = driver.title.strip().lower()
        current_url = driver.current_url.lower()

        if (
            "login" in title or "sign-on" in title or "sign in" in title or "autenticação" in title
            or "login" in current_url or "signon" in current_url
            or "cmd=login" in current_url or "errorcode=" in current_url
        ):
            print("[ERRO] Cookies não deram acesso (caiu login de novo).")
        else:
            print("[OK] Cookies deram acesso direito ao Monitor.")

    finally:
        driver.quit()        

if __name__ == "__main__":
    # test_collector()
    # test_login_gui()
    test_navegacao_monitor()
    # test_cookies_acessam_monitor()
