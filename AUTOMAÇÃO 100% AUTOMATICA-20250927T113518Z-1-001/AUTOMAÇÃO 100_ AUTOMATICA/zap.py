import os
import time
import shutil
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

def log(message):
    """Função de log compatível com Unicode para Windows"""
    try:
        # Tenta imprimir normalmente (para sistemas com suporte a Unicode)
        print(f"{datetime.now()} - {message}")
    except UnicodeEncodeError:
        # Fallback para Windows sem suporte a Unicode
        cleaned_message = message.encode('ascii', 'replace').decode('ascii')
        print(f"{datetime.now()} - {cleaned_message}")

def fill_date_safely(driver, field_id, date):
    try:
        driver.execute_script(f"document.getElementById('{field_id}').value = '{date}';")
        time.sleep(0.5)
        element = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, field_id)))
        element.clear()
        for char in date:
            element.send_keys(char)
            time.sleep(0.05)
        driver.execute_script(f"""
            var el = document.getElementById('{field_id}');
            el.dispatchEvent(new Event('change'));
            el.dispatchEvent(new Event('blur'));
        """)
        return True
    except Exception as e:
        log(f"Erro ao preencher {field_id}: {e}")
        return False

def wait_for_download_complete(download_folder, timeout=30, check_interval=1):
    log("Aguardando conclusão do download...")
    end_time = time.time() + timeout
    while time.time() < end_time:
        if not any(f.endswith('.crdownload') for f in os.listdir(download_folder)):
            if any(f.lower().endswith('.xlsx') for f in os.listdir(download_folder)):
                return True
        time.sleep(check_interval)
    return False

def main():
    log("Iniciando processo de download")
    
    # Configura o sistema para suportar Unicode no Windows
    if sys.platform == "win32":
        os.system("chcp 65001 > nul")  # Muda para UTF-8 no terminal

    # Lê datas de config.txt
    config_path = os.path.join(os.path.dirname(__file__), "config.txt")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding='utf-8') as f:
            lines = [l.strip() for l in f.read().splitlines() if l.strip()]
        if len(lines) >= 2:
            dataDe, dataAte = lines[0], lines[1]
        else:
            log("config.txt sem datas válidas; usando padrão")
            dataDe = dataAte = datetime.now().strftime("%d/%m/%Y")
    else:
        log("config.txt não encontrado; usando padrão")
        dataDe = dataAte = datetime.now().strftime("%d/%m/%Y")

    DOWNLOAD_FOLDER = os.path.abspath("downloads")
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

    # Configurações do Chrome
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    
    prefs = {
        "download.default_directory": DOWNLOAD_FOLDER,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,
        "safebrowsing.disable_download_protection": True
    }
    options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 20)

    try:
        # Login
        log("Realizando login...")
        driver.get("https://gestao.onitel.com.br/app/login")
        wait.until(EC.presence_of_element_located((By.ID, 'email')))\
            .send_keys("gabrielrocha@onitel.com.br" + Keys.RETURN)
        wait.until(EC.presence_of_element_located((By.ID, 'password')))\
            .send_keys("Rocha@076" + Keys.RETURN)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "vg-button#btn-enter-login"))).click()
        try:
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//button[contains(text(), "Lembrar-me em 10 dias")]')
            )).click()
        except TimeoutException:
            pass
        wait.until(EC.url_contains("/adm.php"))

        # Navegação até Ordens de Serviço
        log("Navegando para ordens de serviço...")
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "submenu_title"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space(text())='Suporte']"))).click()
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(@rel, \"cria_grid('#1_grid','su_oss_chamado'\")]")
        )).click()
        time.sleep(1)

        # Filtrar assunto
        log("Aplicando filtros...")
        campo_busca = wait.until(EC.presence_of_element_located((By.ID, 'assunto')))
        campo_busca.clear()
        campo_busca.send_keys("instalação" + Keys.RETURN)
        time.sleep(1)

        # Preencher datas
        if not fill_date_safely(driver, 'dataDe', dataDe):
            raise Exception("Falha ao preencher data inicial")
        if not fill_date_safely(driver, 'dataAte', dataAte):
            raise Exception("Falha ao preencher data final")

        # Aplicar filtro
        campo_int = wait.until(EC.presence_of_element_located((By.ID, 'su_oss_chamado_apply_filter')))
        campo_int.send_keys("Aplicar" + Keys.RETURN)
        time.sleep(1)

        # Limpar pasta de download
        for f in os.listdir(DOWNLOAD_FOLDER):
            if f.lower().endswith(('.xlsx', '.crdownload')):
                os.remove(os.path.join(DOWNLOAD_FOLDER, f))

        # Solicitar download
        log("Iniciando download...")
        btn_menu = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, ".downloadQueryTriggerIcon .fa-download")
        ))
        driver.execute_script("arguments[0].click()", btn_menu)
        time.sleep(1)
        opcao_xls = wait.until(EC.element_to_be_clickable((
            By.XPATH, 
            "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'baixar consulta em xls')]"
        )))
        opcao_xls.click()

        # Aguardar download e renomear
        if wait_for_download_complete(DOWNLOAD_FOLDER, timeout=20):
            xlsx_files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.lower().endswith('.xlsx')]
            if xlsx_files:
                latest = max(
                    (os.path.join(DOWNLOAD_FOLDER, f) for f in xlsx_files),
                    key=os.path.getctime
                )
                target = os.path.join(DOWNLOAD_FOLDER, "resultado.xlsx")
                if os.path.exists(target):
                    os.remove(target)
                shutil.move(latest, target)
                log("SUCESSO: Arquivo salvo em: " + target)
            else:
                log("ERRO: Nenhum arquivo XLSX encontrado")
        else:
            log("ERRO: Download não finalizado a tempo")

    except Exception as e:
        log(f"ERRO: {e}")
        driver.save_screenshot("erro_zap.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()