# 🚀 GUIA: Deploy em Produção

## 🎯 Headless vs Visual

### ✅ Screenshots funcionam EM AMBOS OS MODOS!

```python
# Screenshots são salvos mesmo em headless:
driver.save_screenshot("storage/logs/antes_refresh.png")  ✅
driver.save_screenshot("storage/logs/highlight_refresh.png")  ✅
driver.save_screenshot("storage/logs/depois_refresh.png")  ✅
```

**Você NÃO precisa ver a janela para ter os screenshots!**

---

## 🔧 Configuração: `config/systems_config.json`

### 🧪 Modo DEBUG (Visual)

Para **desenvolvimento/debug** (vê a navegação acontecendo):

```json
{
  "peoplesoft": {
    "headless": false,  ← Mostra navegador
    "collection_interval": 180,
    "filters": {
      "user_id": "MBENITEZ",
      "process_name": "AJ_BU_PS_CLI"
    }
  }
}
```

**Logs:**
```
👀 Modo VISUAL ativado (com interface)
✓ WebDriver inicializado
```

**Comportamento:**
- ✅ Abre janela do Chrome
- ✅ Você vê tudo acontecendo
- ✅ Vê o highlight vermelho+amarelo
- ✅ Screenshots são salvos
- ⚠️ Consome mais recursos
- ⚠️ Requer servidor com interface gráfica

---

### 🚀 Modo PRODUÇÃO (Headless)

Para **produção** (mais eficiente, sem janela):

```json
{
  "peoplesoft": {
    "headless": true,  ← Sem janela, mais rápido
    "collection_interval": 180,
    "filters": {
      "user_id": "MBENITEZ",
      "process_name": "AJ_BU_PS_CLI"
    }
  }
}
```

**Logs:**
```
🎭 Modo HEADLESS ativado (sem interface visual)
✓ WebDriver inicializado
```

**Comportamento:**
- ✅ Sem janela visível
- ✅ Mais rápido (~20% menos tempo)
- ✅ Menos consumo de memória
- ✅ Screenshots continuam funcionando!
- ✅ Funciona em servidores sem GUI
- ✅ Ideal para produção/cron

---

## 📊 Comparação

| Aspecto | Visual (`false`) | Headless (`true`) |
|---------|------------------|-------------------|
| **Performance** | Normal | +20% mais rápido |
| **Memória** | ~500MB | ~300MB |
| **Screenshots** | ✅ Sim | ✅ Sim |
| **Highlight visível** | ✅ Sim (você vê) | ❌ Não (mas salva) |
| **Debug** | ✅ Fácil | ⚠️ Depende de logs |
| **Servidor sem GUI** | ❌ Não funciona | ✅ Funciona |
| **Produção** | ⚠️ Não ideal | ✅ Ideal |

---

## 🔄 Mudança em Tempo Real

### Opção 1: Editar JSON e Reiniciar ✅

**Passo 1:** Editar `config/systems_config.json`
```json
{
  "peoplesoft": {
    "headless": true,  ← Mude aqui
    "filters": {
      "user_id": "NOVO_USUARIO"  ← Ou mude filtros
    }
  }
}
```

**Passo 2:** Parar o sistema
```bash
Ctrl+C
```

**Passo 3:** Iniciar novamente
```bash
python main.py
```

✅ **Mudanças aplicadas imediatamente!**

---

### Opção 2: API REST (Futuro) 🔮

Criar endpoint para alterar configuração sem reiniciar:

```python
# backend/routes.py (FUTURO)
@app.route('/api/config/peoplesoft', methods=['PUT'])
def update_peoplesoft_config():
    new_config = request.json
    # Atualizar JSON
    # Recarregar coletor
    return {"status": "updated"}
```

```bash
# Usar via curl
curl -X PUT http://localhost:5000/api/config/peoplesoft \
  -H "Content-Type: application/json" \
  -d '{"headless": true, "filters": {"user_id": "NOVO"}}'
```

---

### Opção 3: Interface Web (Futuro) 🎨

Criar modal no dashboard para editar configurações:

```html
<!-- Botão no Dashboard -->
<button onclick="openConfigModal()">⚙️ Configurações</button>

<!-- Modal -->
<div id="configModal">
  <h2>Configurações PeopleSoft</h2>
  
  <label>
    <input type="checkbox" id="headless" />
    Modo Headless (produção)
  </label>
  
  <label>
    User ID: <input type="text" id="user_id" />
  </label>
  
  <label>
    Process Name: <input type="text" id="process_name" />
  </label>
  
  <button onclick="saveConfig()">💾 Salvar</button>
</div>
```

---

## 🎯 Recomendação para Cada Ambiente

### 🧪 Desenvolvimento Local

```json
{
  "headless": false,  ← Ver navegação
  "collection_interval": 60  ← Teste rápido (1 min)
}
```

### 🔬 Testes/QA

```json
{
  "headless": true,  ← Sem janela
  "collection_interval": 180  ← 3 minutos
}
```

### 🚀 Produção

```json
{
  "headless": true,  ← Sem janela
  "collection_interval": 300  ← 5 minutos
}
```

---

## 📸 Screenshots em Produção

### Todos continuam funcionando:

```bash
storage/
└── logs/
    ├── antes_refresh.png        ✅ Salvo em headless
    ├── highlight_refresh.png    ✅ Salvo em headless
    └── depois_refresh.png       ✅ Salvo em headless

storage/
└── screenshots/
    └── peoplesoft/
        └── screenshot_20251104_150705.png  ✅ Salvo em headless
```

**Você pode baixar e ver os screenshots mesmo rodando em headless!**

---

## 🔐 Deploy em Servidor

### Opção 1: Servidor Linux com Cron

```bash
# Instalar Chrome headless
sudo apt-get install chromium-browser chromium-chromedriver

# Configurar cron
crontab -e

# Adicionar linha (executar sempre às 8h, 14h, 20h)
0 8,14,20 * * * cd /path/to/monitor_scheduler && /usr/bin/python3 main.py
```

**Config:**
```json
{
  "headless": true  ← SEMPRE true em servidor
}
```

---

### Opção 2: Docker

```dockerfile
FROM python:3.11-slim

# Instalar Chrome headless
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "main.py"]
```

**Config:**
```json
{
  "headless": true  ← SEMPRE true no Docker
}
```

---

### Opção 3: Systemd Service (Linux)

```ini
# /etc/systemd/system/monitor-scheduler.service
[Unit]
Description=Process Monitor Dashboard
After=network.target

[Service]
Type=simple
User=monitor
WorkingDirectory=/opt/monitor_scheduler
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Ativar serviço
sudo systemctl enable monitor-scheduler
sudo systemctl start monitor-scheduler

# Ver logs
sudo journalctl -u monitor-scheduler -f
```

---

## 🔄 Workflow Recomendado

### 1. Desenvolvimento (Sua Máquina)

```json
{
  "headless": false,  ← Ver navegação
  "collection_interval": 60
}
```

```bash
python main.py
# Vê janela abrir, testa filtros, vê highlight
```

---

### 2. Testes com Headless Local

```json
{
  "headless": true  ← Testar modo produção
}
```

```bash
python main.py
# Não vê janela, mas verifica:
# - Logs estão corretos?
# - Screenshots foram salvos?
# - Métricas estão corretas?
```

---

### 3. Deploy para Servidor

```bash
# Copiar para servidor
scp -r . user@servidor:/opt/monitor_scheduler

# SSH no servidor
ssh user@servidor

cd /opt/monitor_scheduler

# Garantir que headless está true
cat config/systems_config.json
# Deve ter: "headless": true

# Executar
python main.py
```

---

## 🎨 Interface Web para Configuração (FUTURO)

### Proposta de Funcionalidades:

```
Dashboard
├── [⚙️ Configurações]  ← Novo botão
│   └── Modal
│       ├── 🎭 Modo Headless [Toggle]
│       ├── ⏱️ Intervalo [Input: 180s]
│       ├── 📋 Filtros
│       │   ├── User ID [Input]
│       │   ├── Process Name [Input]
│       │   ├── Server [Select]
│       │   └── Run Status [Select]
│       └── [💾 Salvar e Reiniciar]
│
├── [📊 Status]
│   ├── Último refresh: 15:30:00
│   ├── Próximo em: 2min 30s
│   ├── Modo: Headless ✅
│   └── Filtros ativos: 2
│
└── [📸 Screenshots]
    ├── Antes Refresh [Ver]
    ├── Highlight [Ver]
    └── Depois Refresh [Ver]
```

---

## 📝 Checklist de Deploy

### Antes de Deploy:

- [ ] Testar localmente com `headless: false` (debug)
- [ ] Testar localmente com `headless: true` (produção)
- [ ] Verificar screenshots salvos em headless
- [ ] Verificar logs estão corretos
- [ ] Verificar filtros aplicados
- [ ] Verificar métricas extraídas

### No Servidor:

- [ ] Chrome/Chromium instalado
- [ ] ChromeDriver compatível
- [ ] Config com `headless: true`
- [ ] Credenciais corretas no JSON
- [ ] Permissões de arquivo OK
- [ ] Portas liberadas (5000)
- [ ] Logs sendo salvos
- [ ] Screenshots sendo salvos

### Após Deploy:

- [ ] Sistema inicia sem erros
- [ ] Login funciona
- [ ] Filtros aplicados
- [ ] Screenshots salvos
- [ ] Dashboard acessível
- [ ] Métricas atualizando

---

## 💡 Dicas de Produção

### 1. Rotação de Screenshots

```python
# Limpar screenshots antigos (>7 dias)
find storage/logs -name "*.png" -mtime +7 -delete
find storage/screenshots -name "*.png" -mtime +7 -delete
```

### 2. Logs com Rotação

```python
# logging.conf
[handler_file]
class=handlers.RotatingFileHandler
maxBytes=10485760  # 10MB
backupCount=5
```

### 3. Monitoramento

```bash
# Verificar se está rodando
ps aux | grep python | grep main.py

# Ver uso de recursos
top -p $(pgrep -f "python main.py")
```

---

## 🎉 Resumo

| Uso | Config | Onde |
|-----|--------|------|
| **Debug** | `headless: false` | Sua máquina |
| **Teste Local** | `headless: true` | Sua máquina |
| **Produção** | `headless: true` | Servidor |

✅ **Screenshots funcionam em todos os modos!**  
✅ **Mude via JSON e reinicie**  
✅ **Futuro: Interface web para configurar**  

**Agora pode testar em headless e depois fazer deploy! 🚀**
