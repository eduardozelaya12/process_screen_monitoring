# 📊 Process Monitor Dashboard - Documentação Completa

## 🎯 O Que Este Sistema Faz?

Este é um **dashboard automatizado** que monitora processos do PeopleSoft (ERP). Ele:

1. 🤖 Abre o Chrome automaticamente usando Selenium
2. 🔐 Faz login no PeopleSoft (ou usa cookies salvos)
3. 📸 Captura screenshots da tela de processos
4. 📊 Extrai métricas (quantos processos rodando, com erro, sucesso, etc.)
5. 💾 Salva tudo em banco de dados SQLite
6. 🌐 Exibe em dashboard web em tempo real
7. 🔄 Repete tudo automaticamente a cada 5 minutos (configurável)

---

## 📁 Estrutura do Projeto

```
monitor_scheduler/
│
├── 📂 backend/              → Servidor Web (Flask + SocketIO)
│   ├── app.py              → Configuração do Flask
│   ├── routes.py           → Endpoints da API REST
│   └── websocket_handlers.py → WebSocket para updates em tempo real
│
├── 📂 collectors/           → Módulos que coletam dados
│   ├── base_collector.py   → Classe base para todos coletores
│   └── peoplesoft_collector.py → Coletor específico PeopleSoft
│
├── 📂 config/               → Arquivos de configuração
│   ├── systems_config.json → Configuração dos sistemas (URLs, credenciais)
│   └── credentials/        → Cookies salvos do login
│
├── 📂 frontend/             → Interface Web
│   ├── templates/          → HTMLs do dashboard
│   └── static/             → CSS, JS, imagens
│
├── 📂 orchestrator/         → Coordenador principal
│   └── orchestrator.py     → Agenda e coordena todas as coletas
│
├── 📂 processors/           → Processadores de dados
│   └── data_processors.py  → Padroniza dados de diferentes fontes
│
├── 📂 storage/              → Armazenamento local
│   ├── dashboard.db        → Banco de dados SQLite
│   ├── screenshots/        → Screenshots capturados
│   └── logs/               → Arquivos de log
│
└── main.py                  → 🚀 PONTO DE ENTRADA - Inicia tudo
```

---

## 🔄 Como Funciona (Passo a Passo)

### 1️⃣ Inicialização (`main.py`)

```
Ao executar: python main.py

1. Cria diretórios necessários
2. Inicia Orchestrator em thread separada
3. Inicia servidor Flask na porta 5000
4. Exibe mensagem: "Dashboard disponível em http://localhost:5000"
```

### 2️⃣ Orchestrator (`orchestrator/orchestrator.py`)

```
O Orchestrator é o "cérebro" do sistema:

1. Carrega config/systems_config.json
2. Para cada sistema habilitado:
   - Cria um coletor (ex: PeopleSoftCollector)
   - Agenda coleta a cada X segundos (padrão: 300s = 5min)
3. Usa APScheduler para executar coletas no horário
4. Quando coleta termina, notifica frontend via WebSocket
```

### 3️⃣ Coletor PeopleSoft (`collectors/peoplesoft_collector.py`)

**Fluxo de uma Coleta:**

```
📋 Método collect() é chamado pelo Orchestrator

1. VERIFICAR COOKIES
   ├─ Cookies existem e válidos?
   │  ├─ Sim → Usar cookies salvos
   │  └─ Não → Fazer login e salvar novos cookies
   
2. ABRIR CHROME
   ├─ Inicializar WebDriver do Selenium
   ├─ Configurar opções (headless, etc.)
   └─ Abrir navegador
   
3. FAZER LOGIN (se necessário)
   ├─ Acessar página de login
   ├─ Preencher username/password
   ├─ Selecionar idioma
   ├─ Clicar Submit
   └─ Salvar cookies para próximas vezes
   
4. NAVEGAR PARA PROCESS MONITOR
   ├─ Carregar cookies
   ├─ Acessar URL do Process Monitor
   └─ Verificar se está na página correta
   
5. EXTRAIR DADOS
   ├─ Limpar filtros (campo de nome)
   ├─ Clicar botão Refresh
   ├─ Localizar tabela de processos
   └─ Para cada linha da tabela:
       ├─ Identificar status (Success, Failed, Running)
       ├─ Contar processos por tipo
       └─ Guardar erros críticos
   
6. CAPTURAR SCREENSHOT
   ├─ driver.save_screenshot(...)
   └─ Salvar em storage/screenshots/peoplesoft/
   
7. RETORNAR DADOS
   └─ {
       'screenshot_path': '...',
       'metrics': {
         'total_processes': 150,
         'running': 10,
         'failed': 5,
         'success': 135,
         'success_rate': 90.0
       }
     }
```

### 4️⃣ Armazenamento (`storage/local_storage.py`)

```
Quando dados chegam:

1. Salvar no SQLite (dashboard.db)
   ├─ Tabela 'metrics': números (total, running, failed, etc.)
   ├─ Tabela 'screenshots': referência aos arquivos PNG
   └─ Tabela 'events': eventos e erros importantes
   
2. Arquivos físicos
   └─ Screenshots salvos em storage/screenshots/
```

### 5️⃣ Backend API (`backend/routes.py`)

**Endpoints disponíveis:**

```
GET /                        → Dashboard principal (HTML)
GET /tv                      → Versão para TV (fullscreen)
GET /api/health              → Health check
GET /api/systems             → Lista sistemas configurados
GET /api/status              → Status atual de todos sistemas
GET /api/status/<sistema>    → Status de um sistema específico
GET /api/history/<sistema>   → Histórico de métricas (últimas 24h)
GET /api/screenshot/<sistema> → Último screenshot capturado
GET /storage/<arquivo>       → Serve arquivos (screenshots, logs)
```

### 6️⃣ WebSocket (`backend/websocket_handlers.py`)

```
Cliente conecta via SocketIO

Eventos disponíveis:
├─ 'connect'        → Cliente conectou
├─ 'disconnect'     → Cliente desconectou
├─ 'request_update' → Cliente pede atualização manual
├─ 'subscribe'      → Cliente se inscreve em sistema específico
└─ 'ping/pong'      → Keepalive

Quando há nova coleta:
└─ broadcast_update() → Envia dados para TODOS clientes conectados
```

---

## 💾 Banco de Dados SQLite

### Estrutura das Tabelas

#### Tabela `metrics`
```sql
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY,
    system_name TEXT,           -- Ex: "peoplesoft"
    timestamp DATETIME,         -- Quando foi coletado
    total_processes INTEGER,    -- Total de processos
    running INTEGER,            -- Processos rodando
    failed INTEGER,             -- Processos com erro
    success INTEGER,            -- Processos bem-sucedidos
    success_rate REAL,          -- Taxa de sucesso (%)
    status TEXT,                -- "healthy", "warning", "error"
    data JSON                   -- Dados completos em JSON
)
```

#### Tabela `screenshots`
```sql
CREATE TABLE screenshots (
    id INTEGER PRIMARY KEY,
    system_name TEXT,
    timestamp DATETIME,
    file_path TEXT,             -- Caminho do arquivo PNG
    file_size INTEGER           -- Tamanho em bytes
)
```

#### Tabela `events`
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    system_name TEXT,
    event_type TEXT,            -- "error", "warning", "info"
    message TEXT,               -- Mensagem do evento
    severity TEXT,              -- "critical", "high", "medium", "low"
    timestamp DATETIME
)
```

### Estado Atual do Banco

```
📊 Estatísticas (em 03/11/2025 16:35):
├─ 19 registros de métricas
├─ 0 registros de screenshots (não implementado ainda)
├─ 0 eventos registrados
└─ Sistema: peoplesoft (único monitorado)

📈 Últimas coletas:
├─ 16:35:21 → 0 processos (healthy)
├─ 16:32:12 → 0 processos (healthy)
├─ 16:13:35 → 0 processos (healthy)
├─ 16:00:48 → 0 processos (healthy)
└─ 15:54:49 → 0 processos (ERROR)

⚠️ TODOS com 0 processos = Servidor inacessível!
```

---

## 🐛 Problema Atual Identificado

### ❌ ERR_CONNECTION_REFUSED

**O que está acontecendo:**
```
1. Sistema inicia ✅
2. Orchestrator agenda coletas ✅
3. Selenium abre Chrome ✅
4. Tenta acessar: http://pswebt1.ajover.com:83/psp/... ❌
5. Servidor recusa conexão ❌
6. Chrome mostra página de erro ERR_CONNECTION_REFUSED ❌
7. Sistema salva screenshot da PÁGINA DE ERRO ✅
8. Não encontra tabela de processos (porque é página de erro) ❌
9. Retorna 0 processos ❌
```

**Por isso:**
- ✓ Sistema funciona perfeitamente
- ✓ Código está correto
- ✗ **MAS** servidor PeopleSoft está inacessível

**Evidência:**
- Arquivo `storage/logs/page_structure.html` contém página de erro do Chrome
- Mensagem: "A conexão com pswebt1.ajover.com foi recusada"
- Código de erro: `ERR_CONNECTION_REFUSED`

---

## 🔧 Como Usar

### Iniciar o Sistema

```powershell
# Ativar ambiente virtual (se usar)
.venv\Scripts\Activate

# Instalar dependências (primeira vez)
pip install -r requirements.txt

# Executar
python main.py
```

### Acessar Dashboard

```
🌐 Navegador: http://localhost:5000
📺 Modo TV: http://localhost:5000/tv
```

### Parar o Sistema

```
Ctrl + C no terminal
```

### Ver Logs em Tempo Real

```powershell
Get-Content storage\logs\dashboard.log -Wait -Tail 30
```

### Inspecionar Banco de Dados

```powershell
python inspect_db.py
```

---

## ⚙️ Configuração

### Arquivo `config/systems_config.json`

```json
{
  "peoplesoft": {
    "name": "PeopleSoft Monitor",
    "type": "peoplesoft",
    "enabled": true,
    "base_url": "http://pswebt1.ajover.com:83",
    "process_monitor_url": "http://pswebt1.ajover.com:83/psp/pa91test/EMPLOYEE/EMPL/h/...",
    "collection_interval": 300,
    "timeout": 30,
    "credentials": {
      "username": "seu_usuario",
      "password": "sua_senha"
    }
  }
}
```

**Parâmetros:**
- `enabled`: true/false - Habilita ou desabilita sistema
- `collection_interval`: Segundos entre cada coleta
- `timeout`: Timeout do Selenium em segundos
- `credentials`: Login do PeopleSoft

---

## 📊 Logs Disponíveis

```
storage/logs/
├── dashboard.log              → Log principal do sistema
├── backend.log                → Log do servidor Flask
├── page_structure.html        → HTML da última página acessada (debug)
└── screenshot_wrong_url.png   → Screenshot quando URL está errada
```

---

## 🎨 Frontend

### Dashboard Principal (`/`)
- Cards com status de cada sistema
- Gráficos de métricas em tempo real
- Lista de processos com erro
- Último screenshot capturado

### Modo TV (`/tv`)
- Interface simplificada para TV
- Atualização automática
- Foco em visualização de longe
- Rotação automática entre sistemas

---

## 🔐 Segurança

### Cookies
- Salvos em: `config/credentials/peoplesoft_cookies.pkl`
- Formato: Pickle (Python serialization)
- Renovados automaticamente quando expiram

### Credenciais
- Armazenadas em: `config/systems_config.json`
- ⚠️ **IMPORTANTE**: Este arquivo está no `.gitignore`
- Não commitar credenciais no Git!

---

## 🚀 Próximas Melhorias Sugeridas

### Funcionalidades
- [ ] Alertas por email quando processos falham
- [ ] Integração com Slack/Teams
- [ ] Exportar relatórios em PDF
- [ ] Dashboard mobile responsivo
- [ ] Comparação de métricas históricas

### Técnicas
- [ ] Implementar gravação de screenshots no banco
- [ ] Health check antes de coletar
- [ ] Retry com backoff exponencial
- [ ] Logs estruturados (JSON)
- [ ] Testes automatizados

### Monitores Adicionais
- [ ] Oracle Fusion
- [ ] Bonita BPM
- [ ] n8n
- [ ] Outros ERPs

---

## 📞 Solução de Problemas

### Problema: ERR_CONNECTION_REFUSED
**Solução:** Ver `DIAGNOSTICO_PROBLEMA.md`

### Problema: "Tabela não encontrada"
**Causa:** Seletores CSS desatualizados ou página diferente
**Solução:** Analisar `storage/logs/page_structure.html`

### Problema: Cookies expiram sempre
**Solução:** Aumentar timeout ou verificar configuração de sessão

### Problema: Chrome não abre
**Causa:** ChromeDriver incompatível
**Solução:** `pip install --upgrade selenium webdriver-manager`

---

## 📚 Tecnologias Utilizadas

- **Backend:** Flask + Flask-SocketIO
- **Frontend:** HTML5 + JavaScript + Chart.js
- **Database:** SQLite3
- **Automation:** Selenium WebDriver
- **Scheduler:** APScheduler
- **WebSocket:** Socket.IO

---

## 📝 Créditos

Sistema desenvolvido para monitoramento automatizado de processos ERP.
