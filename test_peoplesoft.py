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
        try:
            driver.switch_to.default_content()
            WebDriverWait(driver, 5).until(
                EC.frame_to_be_available_and_switch_to_it((By.NAME, "ptifrmtgtframe"))
            )
            print(">> Switch para iframe ptifrmtgtframe OK")
        except Exception:
            print(">> Não foi possível trocar para iframe; tentando no contexto atual…")

        # Perguntar filtros ao usuário
        print("\n=== Filtros opcionais (pressione Enter para pular) ===")
        server_val = input("Server (ex.: PSUNX, AJNODE4B…): ").strip()
        run_status_val = input(
            "Run Status (vazio/1 Cancel, 3 Error, 9 Success, 10 No Success, 7 Processing, 17 Warning… informe o valor numérico): "
        ).strip()
        type_val = input("Type (ex.: Application Engine, PSJob, SQR Report…): ").strip()
        dist_status_val = input(
            "Distribution Status (vazio/5 Posted/3 Generated/4 Not Posted/2 Processing… informe o valor numérico): "
        ).strip()
        time_value = input("Time Filter valor (número, ex.: 1): ").strip()
        time_unit = input("Time Filter unidade (0 All / 1 Days / 2 Hours / 3 Minutes / 4 Years): ").strip()

        # Aplicar filtros se fornecidos
        def set_select_by_id(select_id: str, value_or_text: str):
            try:
                elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, select_id))
                )
                sel = Select(elem)
                # Primeiro tenta por value; se falhar, tenta por texto visível
                try:
                    sel.select_by_value(value_or_text)
                except Exception:
                    sel.select_by_visible_text(value_or_text)
                return True
            except Exception as e:
                print(f"[Aviso] Não foi possível ajustar {select_id}: {e}")
                return False

        if server_val:
            set_select_by_id("PMN_FILTER_WRK_SERVERNAME", server_val)

        if run_status_val:
            set_select_by_id("PMN_FILTER_WRK_RUNSTATUS", run_status_val)

        if type_val:
            set_select_by_id("PMN_FILTER_WRK_PRCSTYPE", type_val)

        if dist_status_val:
            set_select_by_id("PMN_FILTER_WRK_DISTSTATUS", dist_status_val)

        if time_value:
            try:
                tv = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "PMN_FILTER_WRK_PT_FILTERVALUE"))
                )
                tv.clear()
                tv.send_keys(time_value)
            except Exception as e:
                print(f"[Aviso] Não foi possível ajustar PMN_FILTER_WRK_PT_FILTERVALUE: {e}")

        if time_unit:
            set_select_by_id("PMN_FILTER_WRK_PT_FILTERUNIT", time_unit)

        # Clicar Refresh
        try:
            refresh_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "REFRESH_BTN"))
            )
            driver.execute_script("arguments[0].click();", refresh_btn)
            print(">> Filtros aplicados; clicado Refresh")
            time.sleep(4)
        except Exception as e:
            print(f"[Aviso] Não foi possível clicar em Refresh: {e}")

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
