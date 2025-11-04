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
        
        # Server
        server_val = input("\n2. Server (ex.: PSUNX, AJNODE4B, AJNODE4C...): ").strip()
        
        # Run Status
        print("\n3. Run Status:")
        print("   1=Cancel, 3=Error, 7=Processing, 8=Cancelled")
        print("   9=Success, 10=No Success, 17=Warning, 18=Blocked")
        run_status_val = input("   Valor: ").strip()
        
        # Type
        print("\n4. Type:")
        print("   Application Engine, PSJob, SQR Report, Crystal...")
        type_val = input("   Valor: ").strip()
        
        # Distribution Status
        print("\n5. Distribution Status:")
        print("   2=Processing, 3=Generated, 4=Not Posted, 5=Posted, 9=Pending")
        dist_status_val = input("   Valor: ").strip()
        
        # Instance Range
        instance_from = input("\n6. Instance From (número, ex.: 7997100): ").strip()
        instance_to = input("   Instance To (número, ex.: 7997200): ").strip()
        
        # Time Filter
        print("\n7. Time Filter:")
        print("   Type: 0=Last (padrão), 1=Date Range")
        time_filter_type = input("   Type: ").strip()
        time_value = input("   Value (número, ex.: 70): ").strip()
        print("   Unit: 0=All, 1=Days, 2=Hours, 3=Minutes, 4=Years")
        time_unit = input("   Unit: ").strip()
        
        print("\n" + "="*60)

        # Aplicar filtros se fornecidos
        def set_select_by_id(select_id: str, value_or_text: str):
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
            """Define valor em campo de texto"""
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
        
        def search_user_id_modal(user_id: str):
            """Busca User ID usando o modal de lookup"""
            try:
                print(f"\n>> Buscando User ID '{user_id}' via modal...")
                
                # 1. Clicar na lupa para abrir modal
                print("   1. Clicando na lupa de User ID...")
                lupa = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "PMN_FILTER_WRK_WS_OPRID$prompt"))
                )
                driver.execute_script("arguments[0].click();", lupa)
                time.sleep(2)
                
                # 2. Preencher campo de busca no modal
                print("   2. Preenchendo campo de busca...")
                search_field = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "PMN_OPRID_VW_OPRID"))
                )
                search_field.clear()
                search_field.send_keys(user_id)
                
                # 3. Clicar no botão Look Up
                print("   3. Clicando em Look Up...")
                lookup_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "#ICSearch"))
                )
                driver.execute_script("arguments[0].click();", lookup_btn)
                time.sleep(2)
                
                # 4. Tentar clicar no resultado (se existir)
                print("   4. Procurando resultado...")
                try:
                    # Procurar link com o User ID na tabela de resultados
                    result_link = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, f"//a[contains(@class, 'PSSRCHRESULTS') and contains(text(), '{user_id.upper()}')]"))
                    )
                    driver.execute_script("arguments[0].click();", result_link)
                    print(f"   ✓ User ID '{user_id}' selecionado!")
                    time.sleep(1)
                    return True
                except Exception:
                    print(f"   ⚠️ User ID '{user_id}' não encontrado nos resultados")
                    # Tentar fechar modal clicando em Cancel
                    try:
                        cancel_btn = driver.find_element(By.XPATH, "//input[@value='Cancel']")
                        driver.execute_script("arguments[0].click();", cancel_btn)
                        time.sleep(1)
                    except:
                        pass
                    return False
                    
            except Exception as e:
                print(f"   ❌ ERRO ao buscar User ID: {type(e).__name__}")
                print(f"      Detalhes: {str(e)[:100]}")
                return False
        
        # APLICAR FILTROS
        print("\n" + "="*60)
        print("APLICANDO FILTROS...")
        print("="*60)
        
        # 1. User ID (via modal)
        if user_id_val:
            search_user_id_modal(user_id_val)
        
        # 2. Server
        if server_val:
            print("\n>> Aplicando filtro Server...")
            set_select_by_id("PMN_FILTER_WRK_SERVERNAME", server_val)
        
        # 3. Run Status
        if run_status_val:
            print("\n>> Aplicando filtro Run Status...")
            set_select_by_id("PMN_FILTER_WRK_RUNSTATUS", run_status_val)
        
        # 4. Type
        if type_val:
            print("\n>> Aplicando filtro Type...")
            set_select_by_id("PMN_FILTER_WRK_PRCSTYPE", type_val)
        
        # 5. Distribution Status
        if dist_status_val:
            print("\n>> Aplicando filtro Distribution Status...")
            set_select_by_id("PMN_FILTER_WRK_DISTSTATUS", dist_status_val)
        
        # 6. Instance From/To
        if instance_from:
            print("\n>> Aplicando filtro Instance From...")
            set_text_field("PMN_DERIVED_PRCSINSTANCE", instance_from, "Instance From")
        
        if instance_to:
            print("\n>> Aplicando filtro Instance To...")
            set_text_field("PMN_DERIVED_TO_PRCSINSTANCE", instance_to, "Instance To")
        
        # 7. Time Filter Type
        if time_filter_type:
            print("\n>> Aplicando Time Filter Type...")
            set_select_by_id("PMN_FILTER_WRK_PT_FILTERTYPE", time_filter_type)
        
        # 8. Time Filter Value
        if time_value:
            print("\n>> Aplicando Time Filter Value...")
            set_text_field("PMN_FILTER_WRK_PT_FILTERVALUE", time_value, "Time Filter Value")
        
        # 9. Time Filter Unit
        if time_unit:
            print("\n>> Aplicando Time Filter Unit...")
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
