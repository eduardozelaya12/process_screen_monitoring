# 🔄 COMPARAÇÃO: Teste vs Execução Real

## 📋 Pergunta Principal

**"O `main.py` faz o mesmo que `test_navegacao_monitor()`?"**

### Resposta Curta
**SIM e NÃO** - O fluxo é SIMILAR, mas com diferenças importantes:
- ✅ Ambos fazem login e navegam para o monitor
- ✅ Ambos capturam dados
- ❌ O teste é **INTERATIVO** (pede filtros ao usuário)
- ❌ A execução real é **AUTOMÁTICA** (usa cookies salvos, sem interação)

---

## 🔍 Análise Detalhada

### 1️⃣ `test_navegacao_monitor()` - O QUE ELE FAZ

```python
def test_navegacao_monitor():
    # PASSO 1: Inicializa driver
    collector._init_driver()
    driver = collector.driver
    
    # PASSO 2: FAZ LOGIN SEMPRE (não usa cookies)
    driver.get(collector.base_url)
    driver.find_element(By.ID, "userid").send_keys(username)
    driver.find_element(By.ID, "pwd").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    
    # PASSO 3: Navega para monitor
    driver.get(collector.process_url)
    
    # PASSO 4: Troca para iframe (se necessário)
    driver.switch_to.frame("ptifrmtgtframe")
    
    # PASSO 5: PERGUNTA filtros ao usuário (INTERATIVO)
    server_val = input("Server (ex.: PSUNX): ").strip()
    run_status_val = input("Run Status: ").strip()
    # ... etc
    
    # PASSO 6: Aplica os filtros escolhidos
    if server_val:
        set_select_by_id("PMN_FILTER_WRK_SERVERNAME", server_val)
    if run_status_val:
        set_select_by_id("PMN_FILTER_WRK_RUNSTATUS", run_status_val)
    
    # PASSO 7: Clica Refresh
    driver.find_element(By.ID, "REFRESH_BTN").click()
    
    # PASSO 8: Salva screenshot e HTML
    driver.save_screenshot("storage/logs/navegacao_monitor.png")
    with open("dump_monitor.html", "w") as f:
        f.write(driver.page_source)
    
    # PASSO 9: Fecha browser
    driver.quit()
```

**Características do TESTE:**
- 🎯 **Propósito:** Debug e desenvolvimento
- 👤 **Modo:** INTERATIVO (pede input do usuário)
- 🔐 **Login:** SEMPRE faz login novo (não usa cookies)
- 🎛️ **Filtros:** Usuário escolhe quais aplicar
- 📸 **Screenshot:** 1 único screenshot de debug
- 🔄 **Execução:** Manual, uma vez só
- 🗄️ **Banco:** NÃO salva nada no SQLite

---

### 2️⃣ `main.py` → `PeopleSoftCollector.collect()` - O QUE ELE FAZ

```python
def collect():  # Chamado pelo Orchestrator automaticamente
    # PASSO 1: Verifica cookies existentes
    if not os.path.exists(self.cookies_file):
        self.login_and_save_cookies()  # Login apenas se não há cookies
    
    # PASSO 2: Captura e extrai
    screenshot_path, metrics = self._capture_and_extract()
    
    # Dentro de _capture_and_extract():
    
    # PASSO 3: Inicializa driver
    self._init_driver()
    
    # PASSO 4: CARREGA COOKIES (não faz login!)
    if not self._load_cookies():
        return None, {}  # Se cookies falharem, aborta
    
    # PASSO 5: Navega para monitor
    self.driver.get(self.process_url)
    
    # PASSO 6: LIMPA filtros automaticamente (não pergunta)
    self._clear_name_filter()  # Limpa campo de nome e clica Refresh
    
    # PASSO 7: Extrai métricas da página
    metrics = self._extract_metrics_from_page()
    # - Procura tabela de processos
    # - Conta total, running, failed, success
    # - Calcula success_rate
    
    # PASSO 8: Salva screenshot
    screenshot_path = f"storage/screenshots/peoplesoft/screenshot_{timestamp}.png"
    self.driver.save_screenshot(screenshot_path)
    
    # PASSO 9: Retorna dados (não fecha driver ainda)
    return screenshot_path, metrics

# De volta ao Orchestrator:
# PASSO 10: Salva no banco SQLite
self.storage.save_metrics(system_name, processed_data)

# PASSO 11: Notifica frontend via WebSocket
self._broadcast_update(system_name, processed_data)
```

**Características da EXECUÇÃO REAL:**
- 🎯 **Propósito:** Monitoramento contínuo em produção
- 🤖 **Modo:** AUTOMÁTICO (sem interação humana)
- 🔐 **Login:** USA COOKIES salvos (login só na primeira vez)
- 🎛️ **Filtros:** LIMPA todos os filtros (mostra tudo)
- 📸 **Screenshot:** Salvo com timestamp em storage/screenshots/
- 🔄 **Execução:** A cada 5 minutos (300s), infinitamente
- 🗄️ **Banco:** SALVA métricas no SQLite
- 🌐 **WebSocket:** Notifica frontend automaticamente

---

## 📊 Comparação Lado a Lado

| Aspecto | `test_navegacao_monitor()` | `main.py` (Produção) |
|---------|---------------------------|----------------------|
| **Quando executar?** | Manual: `python test_peoplesoft.py` | Automático: `python main.py` |
| **Login** | Sempre faz login novo | Usa cookies (login só 1x) |
| **Filtros** | Pergunta ao usuário | Limpa tudo (sem filtros) |
| **Frequência** | 1 vez só | A cada 5 minutos |
| **Interação** | ✅ INTERATIVO | ❌ SEM interação |
| **Extração de dados** | ❌ NÃO extrai | ✅ Extrai métricas |
| **Salva no banco** | ❌ NÃO | ✅ SIM (SQLite) |
| **Screenshot** | `logs/navegacao_monitor.png` | `screenshots/peoplesoft/screenshot_TIMESTAMP.png` |
| **HTML dump** | ✅ SIM (`dump_monitor.html`) | ⚠️ Só em caso de erro |
| **WebSocket** | ❌ NÃO | ✅ Notifica clientes |
| **Fecha browser** | ✅ Imediatamente (`driver.quit()`) | ✅ No finally de `_capture_and_extract` |
| **Objetivo** | 🔧 Debug/Desenvolvimento | 🚀 Produção/Monitoramento |

---

## 🎯 O Que Cada Um Deve Fazer

### `test_navegacao_monitor()` - PARA DEBUG
```
✅ Usar quando:
- Testando login manualmente
- Verificando se consegue acessar o monitor
- Debugando problemas de conexão
- Experimentando diferentes filtros
- Analisando estrutura da página (HTML dump)

❌ NÃO usar para:
- Monitoramento contínuo
- Extração automática de dados
- Salvar no banco de dados
```

### `main.py` - PARA PRODUÇÃO
```
✅ Usar quando:
- Quer monitoramento automático 24/7
- Precisa de histórico no banco
- Quer dashboard web em tempo real
- Sistema deve rodar sozinho sem intervenção

❌ NÃO usar para:
- Debug de problemas de login
- Testar configurações novas
- Experimentar filtros diferentes
```

---

## 🔄 Fluxo Completo: O Que Acontece Quando Você Executa `main.py`

```
┌─────────────────────────────────────────────────────────────┐
│ python main.py                                              │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ main.py inicializa                                          │
│ - Cria diretórios                                           │
│ - Inicia Orchestrator em thread separada                   │
│ - Inicia Flask server                                       │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ Orchestrator.start()                                        │
│ - Carrega config/systems_config.json                        │
│ - Cria PeopleSoftCollector                                  │
│ - Agenda job: executar a cada 300s                         │
│ - EXECUTA IMEDIATAMENTE (next_run_time=now)                │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ PRIMEIRA EXECUÇÃO (t=0s)                                    │
│ PeopleSoftCollector.collect()                               │
└─────────────────────────────────────────────────────────────┘
                         ↓
         ┌───────────────┴───────────────┐
         ↓                               ↓
    Cookies existem?                 Cookies NÃO existem?
         │                               │
         ↓                               ↓
    Usa cookies                   login_and_save_cookies()
    (pula login)                   - Abre Chrome
                                   - Faz login
                                   - Salva cookies
                                   ↓
         └───────────────┬───────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ _capture_and_extract()                                      │
│ 1. Inicializa Chrome                                        │
│ 2. Carrega cookies                                          │
│ 3. Acessa process_url                                       │
│ 4. Limpa filtros (campo nome)                               │
│ 5. Clica Refresh                                            │
│ 6. Extrai métricas da tabela                                │
│ 7. Salva screenshot                                         │
│ 8. Fecha Chrome                                             │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ De volta ao Orchestrator                                    │
│ 1. Recebe dados do collector                                │
│ 2. Processa e padroniza (DataProcessor)                     │
│ 3. Salva no SQLite (LocalStorage)                           │
│ 4. Atualiza StatusTracker                                   │
│ 5. Notifica frontend via WebSocket                          │
└─────────────────────────────────────────────────────────────┘
                         ↓
         ⏰ Aguarda 300 segundos (5 minutos)
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ SEGUNDA EXECUÇÃO (t=300s)                                   │
│ Repete todo o processo                                      │
│ (mas AGORA usa cookies, não faz login de novo!)            │
└─────────────────────────────────────────────────────────────┘
                         ↓
         ⏰ Aguarda mais 300 segundos
                         ↓
                    (loop infinito)
```

---

## 🐛 Diferenças Críticas para Debug

### Por Que o Teste Pode Funcionar e a Produção Falhar?

#### 1. **Filtros**
```python
# TESTE: Permite escolher filtros específicos
server_val = input("Server: ")  # Pode filtrar por servidor específico

# PRODUÇÃO: Limpa TODOS os filtros
self._clear_name_filter()  # Remove filtros, mostra TUDO
```

**Impacto:** Se o monitor tem muitos processos, a tabela pode demorar para carregar ou ter estrutura diferente.

#### 2. **Timing**
```python
# TESTE: Tempos fixos e maiores
time.sleep(4)  # Espera 4s após cada ação

# PRODUÇÃO: Tempos menores
time.sleep(3)  # Espera 3s
```

**Impacto:** Em rede lenta, produção pode tentar extrair antes da página carregar.

#### 3. **Cookies vs Login**
```python
# TESTE: Login fresco toda vez
driver.get(base_url)
# ... preenche formulário

# PRODUÇÃO: Usa cookies (mais rápido, mas pode expirar)
self._load_cookies()
```

**Impacto:** Cookies podem expirar durante o dia, causando falhas intermitentes.

#### 4. **Tratamento de Erros**
```python
# TESTE: Mostra erro e para
try:
    # código
except Exception as e:
    print(f"[ERRO] {e}")
    driver.quit()  # PARA AQUI

# PRODUÇÃO: Tenta recuperar
try:
    # código
except Exception as e:
    logger.warning("Falha, tentando relogin...")
    self.login_and_save_cookies()  # TENTA RECUPERAR
    # tenta novamente
```

**Impacto:** Produção é mais resiliente, mas pode mascarar problemas.

---

## 🛠️ Quando Usar Cada Teste

### Cenário 1: "Não consigo acessar o PeopleSoft"
```bash
# Use o teste básico de login
python test_peoplesoft.py  # Descomente test_login_gui()
```

### Cenário 2: "Login funciona, mas não vejo os processos"
```bash
# Use o teste de navegação
python test_peoplesoft.py  # Usa test_navegacao_monitor() atual
# Ele vai te permitir experimentar filtros diferentes
```

### Cenário 3: "Cookies não funcionam"
```bash
# Use o teste de cookies
python test_peoplesoft.py  # Descomente test_cookies_acessam_monitor()
```

### Cenário 4: "Quero rodar em produção"
```bash
# Use o main.py
python main.py
```

---

## 📝 Resumo Executivo

### ✅ O Que `test_navegacao_monitor()` FAZ
1. Faz login manual (sempre)
2. Navega para o monitor
3. **PERGUNTA** quais filtros aplicar (INTERATIVO)
4. Aplica os filtros escolhidos
5. Salva screenshot de debug
6. Salva HTML completo
7. Fecha e termina

### ✅ O Que `main.py` FAZ
1. Usa cookies (login só na primeira vez)
2. Navega para o monitor
3. **LIMPA** todos os filtros (automático)
4. Extrai métricas (contagem de processos)
5. Salva screenshot com timestamp
6. **SALVA NO BANCO SQLite**
7. **NOTIFICA FRONTEND via WebSocket**
8. **REPETE A CADA 5 MINUTOS**

### 🎯 Resposta Final

> **"O main.py faz o que seria test_navegacao_monitor?"**

**SIM**, o fluxo básico é o mesmo (login → navegar → capturar), **MAS**:

- ❌ `test_navegacao_monitor` é para **DEBUG** (interativo, 1 vez)
- ✅ `main.py` é para **PRODUÇÃO** (automático, 24/7)

O teste **não extrai métricas nem salva no banco** - ele apenas verifica se consegue acessar a página.

O `main.py` faz muito mais:
- ✅ Extrai dados reais da tabela
- ✅ Salva no banco
- ✅ Serve dashboard web
- ✅ Executa continuamente
- ✅ Notifica clientes em tempo real

---

## 💡 Recomendação

**Para desenvolvimento/debug:**
```bash
python test_peoplesoft.py
```

**Para produção/monitoramento:**
```bash
python main.py
```

**Não misture os dois!** São ferramentas diferentes para propósitos diferentes.
