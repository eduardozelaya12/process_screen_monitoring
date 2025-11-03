import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
try:
	from webdriver_manager.chrome import ChromeDriverManager  # opcional (fallback)
except Exception:  # evita falha se não instalado
	ChromeDriverManager = None


def take_google_screenshot(headless: bool = False) -> str:

	options = webdriver.ChromeOptions()
	options.add_argument('--start-maximized')
	options.add_argument('--disable-blink-features=AutomationControlled')
	options.add_argument('--no-sandbox')
	options.add_argument('--disable-dev-shm-usage')
	options.add_argument('--disable-gpu')
	options.add_experimental_option('excludeSwitches', ['enable-logging'])
	if headless:
		options.add_argument('--headless=new')

	# 1) Tenta Selenium Manager (recomendado no Selenium 4.6+)
	try:
		driver = webdriver.Chrome(options=options)
	except Exception:
		# 2) Fallback: webdriver_manager (se disponível)
		if ChromeDriverManager is None:
			raise
		service = Service(ChromeDriverManager().install())
		driver = webdriver.Chrome(service=service, options=options)
	driver.set_page_load_timeout(30)

	try:
		url = 'https://www.google.com/'
		driver.get(url)

		# Tenta fechar o banner de consentimento (varia por região)
		for selector in [
			"button#L2AGLb",  # EU - "Aceitar tudo"
			"button[aria-label='Accept all']",
			"div[role='none'] form [type='submit']",
			"button[jsname][data-ved]",
		]:
			try:
				btn = WebDriverWait(driver, 3).until(
					EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
				)
				driver.execute_script("arguments[0].click();", btn)
				time.sleep(1)
				break
			except Exception:
				pass

		# Aguarda o título conter "Google"
		try:
			WebDriverWait(driver, 10).until(EC.title_contains('Google'))
		except Exception:
			pass

		os.makedirs('storage/logs', exist_ok=True)
		out_path = 'storage/logs/google_home.png'
		driver.save_screenshot(out_path)
		with open('storage/logs/google_home.html', 'w', encoding='utf-8') as f:
			f.write(driver.page_source)
		return out_path

	finally:
		driver.quit()


if __name__ == '__main__':
	path = take_google_screenshot(headless=False)
	print(f"Screenshot salvo em: {path}")


