# 🚀 Automação de Relatórios – Onitel Telecom

Este projeto foi desenvolvido para o **Setor de Monitoramento da Onitel Telecom** com o objetivo de **automatizar relatórios de SLA**: desde o download no sistema de gestão até a atualização e visualização em tempo real via aplicação web.

Após **5 meses de testes com 100% de aproveitamento**, o setor de Monitoramento está **batendo meta há 3 meses consecutivos** e segue com maior eficiência, padronização e confiabilidade dos dados.

---

## 🔧 Funcionamento do Projeto

O fluxo completo da automação é o seguinte:

1️⃣ **Download automático (`zap.py`)**

* Usa Selenium para acessar o sistema interno da Onitel, realizar login e aplicar filtros.
* Faz o download do relatório em **Excel** de forma automática.
* O arquivo é salvo em `downloads/resultado.xlsx`.

2️⃣ **Tratamento e Banco de Dados (`criar_db.py`)**

* Lê o Excel baixado, limpa e padroniza os dados.
* Converte SLA para número e datas para formato padrão.
* Atualiza o banco de dados **SQLite (`relatorios.db`)** de forma incremental, evitando duplicados.

3️⃣ **Interface Web (`app.py`)**

* Servidor **Flask** que exibe os relatórios em tempo real.
* API REST (`/api/data`) para consulta filtrada (SLA positivo, negativo ou todos).
* Template HTML mostra os relatórios com última atualização.

4️⃣ **Automação Contínua (`scheduler.py`)**

* Executa todo o ciclo (download → processamento → atualização no banco).
* Interface gráfica em Tkinter para configurar datas, iniciar/parar automação e acompanhar logs.
* Atualiza a cada 10 minutos por padrão (ajustável).
* Dispara **alerta sonoro** com `sirene.mp3` caso detecte registros negativos novos.

5️⃣ **Scripts auxiliares**

* `ativar_e_rodar.ps1`: script em PowerShell para iniciar a automação no Windows.
* `launcher.py`: versão simplificada com botões para iniciar a sequência manualmente.

---

## 🛠️ Tecnologias Utilizadas

* **Python 3**
* **Selenium + WebDriver Manager** → automação do navegador
* **Pandas / OpenPyXL** → manipulação e leitura de Excel
* **SQLite3** → banco de dados local
* **Flask** → aplicação web e API
* **Tkinter** → interface gráfica de controle
* **Schedule / Threads** → execução periódica
* **Pystray + Pillow** → integração com ícone de sistema
* **Cryptography** → segurança de credenciais

---

## 📊 Benefícios para o Setor de Monitoramento

* Eliminação de etapas manuais repetitivas.
* Atualização **automática** dos relatórios a cada ciclo.
* Confiabilidade e padronização dos dados.
* Interface web acessível em rede local.
* Identificação imediata de **registros com SLA abaixo de 90**.
* Alertas automáticos para eventos críticos.

---

## ▶️ Como Rodar o Projeto

### 1. Clone o repositório

```bash
git [clone https://github.com/gabrielpyxp/Onitelautomacao2
cd Onitelautomacao2
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Inicie a automação contínua

```bash
python scheduler.py
```

### 4. Acesse no navegador

```
http://127.0.0.1:5000
```

---

## 📂 Estrutura do Projeto

```
automacao-onitel/
│── zap.py             # Automação de login e download do relatório XLSX
│── criar_db.py        # Processamento e atualização do banco SQLite
│── app.py             # Aplicação Flask com API e interface web
│── scheduler.py       # Automação contínua com GUI e integração Flask
│── launcher.py        # Execução manual simplificada
│── ativar_e_rodar.ps1 # Script PowerShell para iniciar automação
│── requirements.txt   # Lista de dependências
│── config.txt         # Datas padrão de consulta
│── relatorios.db      # Banco SQLite (gerado automaticamente)
│── downloads/         # Pasta onde relatórios XLSX são salvos
│── static/sirene.mp3  # Alerta sonoro
│── templates/index.html # Template HTML da aplicação
```

---

## 📈 Resultados

* **2 meses de testes com 100% de aproveitamento**.
* **Setor de Monitoramento batendo meta há 2 meses consecutivos**.
* Fluxo **100% automatizado**, confiável e contínuo.

---

## 💡 Objetivo

Garantir que os relatórios de SLA estejam **sempre atualizados, padronizados e acessíveis em tempo real**, trazendo mais eficiência e escalabilidade ao setor de Monitoramento da Onitel Telecom.
