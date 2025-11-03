import pickle
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json

def debug_peoplesoft_page():
    """Debugar estrutura da página PeopleSoft"""
    print("\n" + "="*60)
    print("DEBUG: Estrutura da Página PeopleSoft")
    print("="*60 + "\n")
    
    # Carregar config
    with open('config/systems_config.json', 'r') as f:
        config = json.load(f)
    
    ps_config = config['peoplesoft']
    
    # Inicializar driver
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    # NÃO usar headless para ver a página
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Carregar cookies
        driver.get(ps_config['base_url'])
        time.sleep(2)
        
        with open('config/credentials/peoplesoft_cookies.pkl', 'rb') as f:
            cookies = pickle.load(f)
        
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except:
                pass
        
        # Navegar para página de processos
        print(f"Navegando para: {ps_config['process_monitor_url']}")
        driver.get(ps_config['process_monitor_url'])
        time.sleep(5)
        
        # Limpar filtros
        try:
            campo_nome = driver.find_element(By.ID, "PMN_FILTER_WRK_PRCSNAME")
            campo_nome.clear()
        except:
            pass
        
        try:
            botao_refresh = driver.find_element(By.ID, "REFRESH_BTN")
            driver.execute_script("arguments[0].click();", botao_refresh)
            time.sleep(4)
        except:
            pass
        
        print("\n" + "-"*60)
        print("INFORMAÇÕES DA PÁGINA:")
        print("-"*60)
        print(f"URL atual: {driver.current_url}")
        print(f"Título: {driver.title}")
        
        # Salvar HTML completo
        html_path = "storage/logs/page_structure.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"\n✓ HTML salvo em: {html_path}")
        
        # Procurar por todas as tabelas
        print("\n" + "-"*60)
        print("TABELAS ENCONTRADAS:")
        print("-"*60)
        
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"\nTotal de tabelas: {len(tables)}")
        
        for idx, table in enumerate(tables):
            try:
                table_id = table.get_attribute('id')
                table_class = table.get_attribute('class')
                rows = table.find_elements(By.TAG_NAME, "tr")
                
                print(f"\nTabela {idx + 1}:")
                print(f"  ID: {table_id or 'N/A'}")
                print(f"  Class: {table_class or 'N/A'}")
                print(f"  Linhas: {len(rows)}")
                
                # Mostrar primeira linha (cabeçalho)
                if len(rows) > 0:
                    headers = rows[0].find_elements(By.TAG_NAME, "th")
                    if headers:
                        header_text = [h.text for h in headers]
                        print(f"  Cabeçalhos: {header_text}")
                    
                    # Mostrar segunda linha (primeira linha de dados)
                    if len(rows) > 1:
                        cells = rows[1].find_elements(By.TAG_NAME, "td")
                        if cells:
                            cell_text = [c.text[:30] for c in cells[:5]]  # Primeiras 5 células
                            print(f"  Primeira linha: {cell_text}")
            except:
                pass
        
        # Procurar por divs com ID relacionado a processo
        print("\n" + "-"*60)
        print("DIVS PRINCIPAIS:")
        print("-"*60)
        
        divs = driver.find_elements(By.CSS_SELECTOR, "div[id*='PROCESS'], div[id*='PMN']")
        print(f"\nTotal de divs relevantes: {len(divs)}")
        
        for idx, div in enumerate(divs[:10]):  # Primeiros 10
            div_id = div.get_attribute('id')
            div_class = div.get_attribute('class')
            print(f"\nDiv {idx + 1}:")
            print(f"  ID: {div_id}")
            print(f"  Class: {div_class}")
        
        # Procurar por iframes
        print("\n" + "-"*60)
        print("IFRAMES:")
        print("-"*60)
        
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"\nTotal de iframes: {len(iframes)}")
        
        for idx, iframe in enumerate(iframes):
            iframe_id = iframe.get_attribute('id')
            iframe_name = iframe.get_attribute('name')
            print(f"\niframe {idx + 1}:")
            print(f"  ID: {iframe_id}")
            print(f"  Name: {iframe_name}")
        
        # Salvar screenshot
        screenshot_path = "storage/logs/debug_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"\n✓ Screenshot salvo em: {screenshot_path}")
        
        print("\n" + "="*60)
        print("Pressione Enter para fechar o navegador...")
        input()
        
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_peoplesoft_page()
