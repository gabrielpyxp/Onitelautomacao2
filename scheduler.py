import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import sqlite3
import subprocess
from flask import Flask, render_template, request, jsonify, send_from_directory
import sys

# --- FLASK APP ---
static_folder = os.path.abspath('static')
app = Flask(__name__, static_folder=static_folder)
LAST_UPDATE = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Armazena os IDs negativos do ciclo anterior
PREVIOUS_NEGATIVE_IDS = set()

# Verifica se o arquivo sirene.mp3 existe e faz log
sirene_path = os.path.join(static_folder, 'sirene.mp3')
if not os.path.exists(sirene_path):
    print(f"[ERRO] sirene.mp3 não encontrado em {sirene_path}")
else:
    print(f"[OK] sirene.mp3 encontrado em {sirene_path}")

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(static_folder, filename)

@app.route('/')
def index():
    return render_template('index.html', last_update=LAST_UPDATE)

@app.route('/api/data')
def get_data():
    global PREVIOUS_NEGATIVE_IDS
    conn = sqlite3.connect('relatorios.db')
    conn.row_factory = sqlite3.Row
    sla_filter = request.args.get('sla_filter')
    # Corrige a query para aplicar WHERE corretamente
    if sla_filter == "positivo":
        query = "SELECT ID, NomeCliente, SLA, Abertura, Status FROM relatorios WHERE SLA >= 90 ORDER BY Abertura DESC"
        params = []
    elif sla_filter == "negativo":
        query = "SELECT ID, NomeCliente, SLA, Abertura, Status FROM relatorios WHERE SLA < 90 ORDER BY Abertura DESC"
        params = []
    else:
        query = "SELECT ID, NomeCliente, SLA, Abertura, Status FROM relatorios ORDER BY Abertura DESC"
        params = []
    cursor = conn.execute(query, params)
    dados = cursor.fetchall()
    conn.close()
    # Detecta IDs negativos novos
    current_negative_ids = set(row['ID'] for row in dados if row['SLA'] < 90)
    new_negative_ids = list(current_negative_ids - PREVIOUS_NEGATIVE_IDS)
    PREVIOUS_NEGATIVE_IDS = current_negative_ids
    return jsonify({'data': [dict(row) for row in dados], 'last_update': LAST_UPDATE, 'new_negative_ids': new_negative_ids})

def start_flask():
    # Permite acesso externo na rede local
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)

# --- FIM FLASK APP ---

# Executa o script para criar o banco de dados
subprocess.run(["python", "criar_db.py"])

class AutomacaoOnitel:
    def __init__(self, root):
        self.root = root
        self.root.title("Automação Onitel - Modo Contínuo")
        self.root.geometry("600x400")
        
        self.driver = None
        self.running = False
        self.cycle_count = 0
        
        self.setup_ui()
        self.load_dates()
        # Inicia o Flask em uma thread separada
        threading.Thread(target=start_flask, daemon=True).start()
    
    def setup_ui(self):
        """Configura a interface gráfica"""
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Controles de data
        date_frame = ttk.LabelFrame(main_frame, text="Período de Consulta", padding=10)
        date_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(date_frame, text="Data Início:").grid(row=0, column=0, padx=5)
        self.start_date = ttk.Entry(date_frame, width=12)
        self.start_date.grid(row=0, column=1, padx=5)
        
        ttk.Label(date_frame, text="Data Fim:").grid(row=0, column=2, padx=5)
        self.end_date = ttk.Entry(date_frame, width=12)
        self.end_date.grid(row=0, column=3, padx=5)
        
        ttk.Button(date_frame, text="Salvar", command=self.save_dates).grid(row=0, column=4, padx=5)
        
        # Controles de execução
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="Iniciar Automação", command=self.start_automation)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Parar Automação", command=self.stop_automation, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Área de logs
        self.log_text = tk.Text(main_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Barra de status
        self.status_var = tk.StringVar(value="Pronto para iniciar")
        ttk.Label(main_frame, textvariable=self.status_var).pack()
        
    def load_dates(self):
        """Carrega as datas do arquivo config.txt"""
        try:
            with open("config.txt", "r") as f:
                dates = f.read().splitlines()
                if len(dates) >= 2:
                    self.start_date.delete(0, tk.END)
                    self.start_date.insert(0, dates[0])
                    self.end_date.delete(0, tk.END)
                    self.end_date.insert(0, dates[1])
        except FileNotFoundError:
            today = datetime.now().strftime("%d/%m/%Y")
            self.start_date.insert(0, today)
            self.end_date.insert(0, today)
    
    def save_dates(self):
        """Salva as datas no arquivo config.txt"""
        with open("config.txt", "w") as f:
            f.write(f"{self.start_date.get()}\n{self.end_date.get()}")
        self.log("Datas salvas com sucesso!")
    
    def log(self, message):
        """Adiciona mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
    
    def start_automation(self):
        """Inicia o processo de automação"""
        if self.running:
            return
            
        self.running = True
        self.cycle_count = 0
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        threading.Thread(target=self.automation_loop, daemon=True).start()
    
    def stop_automation(self):
        """Para a automação"""
        self.running = False
        self.status_var.set("Automação parada")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def automation_loop(self):
        """Loop principal de automação"""
        try:
            self.log("Iniciando navegador...")
            self.init_browser()
            self.do_login()
            
            while self.running:
                self.cycle_count += 1
                self.log(f"\n--- Ciclo {self.cycle_count} ---")
                self.status_var.set(f"Em execução - Ciclo {self.cycle_count}")
                
                try:
                    self.do_download()
                    self.update_database()
                    self.log("Download concluído! Próximo em 10 minutos...")
                except Exception as e:
                    self.log(f"Erro no ciclo: {str(e)}")
                
                for _ in range(600):  # 10 minutos (600 segundos)
                    if not self.running:
                        break
                    time.sleep(1)
            
        except Exception as e:
            self.log(f"Erro fatal: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
            self.stop_automation()
    
    def init_browser(self):
        """Inicializa o navegador Chrome visível e define a pasta de download corretamente"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_experimental_option("detach", True)

        # Define o diretório de download para a pasta correta
        downloads_dir = os.path.abspath("downloads")
        prefs = {
            "download.default_directory": downloads_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            # Desativa proteção de download e verificação de vírus do Chrome
            "safebrowsing.enabled": False,
            "safebrowsing.disable_download_protection": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
    
    def do_login(self):
        self.log("Realizando login...")
        self.driver.get("https://gestao.onitel.com.br/app/login")

        try:
            # Preenche e-mail
            email = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, 'email'))
            )
            email.send_keys("gabrielrocha@onitel.com.br" + Keys.RETURN)

            # Preenche senha
            password = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, 'password'))
            )
            password.send_keys("Rocha@076" + Keys.RETURN)

            # Clica no botão de login principal
            login_btn = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "vg-button#btn-enter-login"))
            )
            login_btn.click()

            # Tratamento avançado para o popup "Lembrar-me"
            try:
                # Espera até que o popup apareça (com timeout reduzido)
                lembrar_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//button[contains(., "Lembrar-me") or contains(., "Lembrar")]')
                    )
                )
                # Tenta clicar normalmente
                try:
                    lembrar_btn.click()
                except Exception:
                    # Se houver overlay, tenta clicar via JavaScript
                    self.driver.execute_script("arguments[0].click();", lembrar_btn)
            except Exception:
                self.log("Popup 'Lembrar-me' não apareceu")
                pass

            # Verifica se o login foi bem sucedido
            WebDriverWait(self.driver, 20).until(
                EC.url_contains("/adm.php")
            )
            self.log("Login realizado com sucesso!")

        except Exception as e:
            self.log(f"Falha no login: {str(e)}")
            self.driver.save_screenshot("erro_login.png")
            raise

    def fill_date_safely(self, driver, field_id, date):
        """Tenta preencher o campo de data de forma robusta, retorna True se conseguir."""
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, field_id))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, field_id)))
            element.click()
            time.sleep(0.2)
            element.clear()
            element.send_keys(Keys.CONTROL + "a")
            element.send_keys(Keys.DELETE)
            time.sleep(0.2)
            element.send_keys(date)
            element.send_keys(Keys.TAB)
            return True
        except Exception as e:
            self.log(f"Erro ao preencher data no campo {field_id}: {str(e)}")
            return False

    def do_download(self):
        try:
            menu = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "submenu_title"))
            )
            self.driver.execute_script("arguments[0].click();", menu)

            suporte = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Suporte')]"))
            )
            self.driver.execute_script("arguments[0].click();", suporte)

            report_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@rel, \"cria_grid('#1_grid','su_oss_chamado'\")]"))
            )
            self.driver.execute_script("arguments[0].click();", report_btn)
            time.sleep(1)

            assunto = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'assunto'))
            )
            assunto.clear()
            assunto.send_keys("instalação" + Keys.RETURN)
            time.sleep(1)

            # Usa a função robusta para preencher as datas
            if not self.fill_date_safely(self.driver, 'dataDe', self.start_date.get()):
                raise Exception("Falha ao preencher data inicial")
            if not self.fill_date_safely(self.driver, 'dataAte', self.end_date.get()):
                raise Exception("Falha ao preencher data final")

            aplicar = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'su_oss_chamado_apply_filter'))
            )
            aplicar.send_keys("Aplicar" + Keys.RETURN)
            time.sleep(1)

            self.log("Iniciando download...")
            download_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".downloadQueryTriggerIcon .fa-download"))
            )
            self.driver.execute_script("arguments[0].click();", download_btn)
            time.sleep(1)

            excel_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'baixar consulta em xls')]"))
            )
            self.driver.execute_script("arguments[0].click();", excel_option)

            self.wait_for_download()

        except Exception as e:
            self.log(f"Erro durante o download: {str(e)}")
            raise
    
    def wait_for_download(self, timeout=60):
        """Aguarda o download completar, remove o anterior e renomeia o novo para resultado.xlsx."""
        downloads_dir = os.path.abspath("downloads")
        target = os.path.join(downloads_dir, "resultado.xlsx")
        start_time = time.time()

        # Remove o arquivo anterior antes de baixar o novo
        if os.path.exists(target):
            try:
                os.remove(target)
                self.log(f"Arquivo antigo removido: {target}")
            except Exception as e:
                self.log(f"Erro ao remover arquivo antigo: {str(e)}")

        while (time.time() - start_time) < timeout:
            files = os.listdir(downloads_dir)
            xlsx_files = [f for f in files if f.lower().endswith('.xlsx')]
            if 'resultado.xlsx' in xlsx_files and not any(f.endswith('.crdownload') for f in files):
                self.log(f"Download salvo como: {target}")
                return True
            xlsx_files = [f for f in xlsx_files if f != 'resultado.xlsx']
            if not any(f.endswith('.crdownload') for f in files) and xlsx_files:
                latest = max(
                    [os.path.join(downloads_dir, f) for f in xlsx_files],
                    key=os.path.getctime
                )
                for attempt in range(5):
                    try:
                        os.rename(latest, target)
                        self.log(f"Download renomeado para: {target}")
                        return True
                    except PermissionError:
                        self.log(f"Arquivo bloqueado por antivírus, tentativa {attempt+1}/5. Aguardando...")
                        time.sleep(3)
                    except Exception as e:
                        self.log(f"Erro ao renomear arquivo: {str(e)}")
                        break
                self.log("Não foi possível renomear o arquivo após várias tentativas.")
                return False
            time.sleep(1)
        self.log("Timeout ao aguardar download")
        return False
    
    def update_database(self):
        """Atualiza o banco de dados com o arquivo baixado de forma incremental, sem sobrescrever registros existentes."""
        try:
            import re
            file_path = os.path.join("downloads", "resultado.xlsx")
            if not os.path.exists(file_path):
                self.log("Arquivo não encontrado para importação")
                return

            self.log("Importando dados para o banco (incremental, limpando tabela antes)...")
            df = pd.read_excel(file_path)
            df = df.rename(columns={
                'Cliente': 'NomeCliente',
                'SLA': 'SLA',
                'Abertura': 'Abertura',
                'Status': 'Status'
            })[['ID', 'NomeCliente', 'SLA', 'Abertura', 'Status']]

            # Conversão de dados
            def clean_sla(value):
                try:
                    if pd.isna(value):
                        return None
                    if isinstance(value, (int, float)):
                        return float(value)
                    cleaned = re.sub(r'[^\d.,-]', '', str(value))
                    cleaned = cleaned.replace(',', '.')
                    return float(cleaned)
                except:
                    return None
            df['SLA'] = df['SLA'].apply(clean_sla)
            df['Abertura'] = pd.to_datetime(df['Abertura'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
            df = df.dropna(subset=['ID', 'NomeCliente', 'SLA', 'Abertura', 'Status'])

            conn = sqlite3.connect('relatorios.db')
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relatorios (
                    ID INTEGER PRIMARY KEY,
                    NomeCliente TEXT,
                    SLA REAL,
                    Abertura TEXT,
                    Status TEXT
                )
            """)
            # Limpa a tabela antes de inserir os novos dados
            cursor.execute("DELETE FROM relatorios")
            conn.commit()
            if not df.empty:
                df.to_sql('relatorios', conn, if_exists='append', index=False)
                self.log(f"Banco atualizado: {len(df)} registros importados (tabela limpa antes)")
            else:
                self.log("Nenhum registro para importar.")
            conn.close()
        except Exception as e:
            self.log(f"Erro ao atualizar banco: {str(e)}")

if __name__ == "__main__":
    # Garante que o template do Flask está disponível
    if not os.path.exists('templates/index.html'):
        with open('templates/index.html', 'w', encoding='utf-8') as f:
            f.write("""
<!DOCTYPE html>
<html lang='pt-br'>
<head>
    <meta charset='UTF-8'>
    <title>Relatórios Onitel</title>
</head>
<body>
    <h1>Relatórios Onitel</h1>
    <p>Última atualização: {{ last_update }}</p>
    <div id="tabela"></div>
    <script>
        fetch('/api/data')
            .then(resp => resp.json())
            .then(data => {
                let html = '<table border=1><tr><th>ID</th><th>Cliente</th><th>SLA</th><th>Abertura</th><th>Status</th></tr>';
                for (const row of data.data) {
                    html += `<tr><td>${row.ID}</td><td>${row.NomeCliente}</td><td>${row.SLA}</td><td>${row.Abertura}</td><td>${row.Status}</td></tr>`;
                }
                html += '</table>';
                document.getElementById('tabela').innerHTML = html;
            });
    </script>
</body>
</html>""")
    root = tk.Tk()
    app = AutomacaoOnitel(root)
    root.mainloop()