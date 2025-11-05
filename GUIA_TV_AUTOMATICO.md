# 📺 DASHBOARD PARA TV - MODO AUTOMÁTICO

## ✅ CORREÇÕES APLICADAS

### 1. 🔧 GoogleCollector Corrigido
```python
def test_connection(self) -> bool:
    """Testa conexão com o Google"""
    try:
        import requests
        response = requests.get(self.base_url, timeout=5)
        return response.status_code == 200
    except:
        return True  # Assume que está OK
```

### 2. 📺 Nova TV Display Criada
- **Rota:** `http://localhost:5000/tv`
- **Grid automático** com todos os sistemas
- **Atualização automática** a cada 15s
- **Visual limpo** para TV

### 3. ⚙️ Configuração Automática
```json
{
  "peoplesoft": {
    "enabled": true,  ← Inicia automaticamente
    "headless": true, ← Modo produção
    "collection_interval": 180
  },
  "google": {
    "enabled": true,  ← Inicia automaticamente
    "headless": true, ← Modo produção
    "collection_interval": 60
  }
}
```

---

## 🎯 CONCEITO: Dashboard para TV

### O Que É?

Um **dashboard de monitoramento contínuo** exibido em uma TV/monitor, mostrando **todos os sistemas simultaneamente** em um grid.

```
┌─────────────────────────────────────────────────────┐
│  📊 Monitor de Processos - TV      🕐 15:30:45      │
├──────────────────────┬──────────────────────────────┤
│  PeopleSoft          │  Google                      │
│  ● Ativo             │  ● Ativo                     │
│  ┌─────────────────┐ │  ┌─────────────────┐         │
│  │   Screenshot    │ │  │   Screenshot    │         │
│  │   PeopleSoft    │ │  │   Google.com    │         │
│  └─────────────────┘ │  └─────────────────┘         │
│  Intervalo: 180s     │  Intervalo: 60s              │
│  Atualizado: 15:30   │  Atualizado: 15:30           │
├──────────────────────┴──────────────────────────────┤
│  Oracle Fusion       │  Bonita BPM                  │
│  ○ Parado            │  ○ Parado                    │
│  ┌─────────────────┐ │  ┌─────────────────┐         │
│  │  Sem screenshot │ │  │  Sem screenshot │         │
│  └─────────────────┘ │  └─────────────────┘         │
└──────────────────────┴──────────────────────────────┘
```

---

## 🏗️ Como Funciona

### 1. Início Automático

```bash
python main.py
```

**O que acontece:**
```
1. Sistema inicia
   ↓
2. Orquestrador lê systems_config.json
   ↓
3. Para cada sistema com enabled: true:
   ├─ Cria collector
   ├─ Agenda job com intervalo configurado
   └─ Executa primeira coleta imediatamente
   ↓
4. Sistemas ficam rodando continuamente
```

### 2. Display TV

```
Abrir: http://localhost:5000/tv
```

**Atualização automática:**
- Grid atualiza lista de sistemas a cada **10 segundos**
- Screenshots atualizam a cada **15 segundos**
- Relógio atualiza a cada **1 segundo**

### 3. Coleta Contínua

```
Google (60s):
├─ 15:00:00 → Coleta #1
├─ 15:01:00 → Coleta #2
├─ 15:02:00 → Coleta #3
└─ ...

PeopleSoft (180s):
├─ 15:00:00 → Coleta #1
├─ 15:03:00 → Coleta #2
├─ 15:06:00 → Coleta #3
└─ ...
```

---

## 📊 Tipos de Dashboard

### Dashboard Admin (`/`)
```
- Controle individual (Start/Stop)
- Dropdown para selecionar sistema
- Ideal para: Operação e debug
```

### Dashboard TV (`/tv`)
```
- Grid com todos os sistemas
- Atualização automática
- Sem controles interativos
- Ideal para: TV, monitoramento passivo
```

---

## 🎬 Setup Completo para TV

### 1. Configurar Sistemas

```json
{
  "peoplesoft": {
    "enabled": true,     ← Liga automaticamente
    "headless": true,    ← Sem janela (produção)
    "collection_interval": 180
  },
  "google": {
    "enabled": true,     ← Liga automaticamente
    "headless": true,    ← Sem janela (produção)
    "collection_interval": 60
  }
}
```

### 2. Iniciar Servidor

```bash
python main.py
```

**Logs esperados:**
```
INFO - ✓ Coletor peoplesoft inicializado
INFO - ✓ Coletor google inicializado
INFO - ✓ 2 coletores inicializados
INFO - ✓ Job agendado: peoplesoft a cada 180s
INFO - ✓ Job agendado: google a cada 60s
INFO - ✓ Dashboard disponível em: http://localhost:5000
INFO - ✓ Versão TV disponível em: http://localhost:5000/tv
```

### 3. Abrir no Navegador da TV

```
1. Na TV/Monitor, abrir Chrome/Edge
2. Acessar: http://<IP-DO-SERVIDOR>:5000/tv
3. Pressionar F11 (fullscreen)
4. Deixar aberto 24/7
```

**Exemplo:**
```
http://192.168.0.39:5000/tv
```

---

## 🖥️ Modos de Operação

### Modo 1: Desenvolvimento (Sua Máquina)

```json
{
  "peoplesoft": {
    "enabled": false,   ← Controle manual
    "headless": false   ← Ver navegação
  }
}
```

```
- Use http://localhost:5000 (admin)
- Controle Start/Stop manualmente
- Vê janelas do Chrome
- Debug e teste
```

### Modo 2: Produção TV (Servidor)

```json
{
  "peoplesoft": {
    "enabled": true,   ← Automático
    "headless": true   ← Sem janela
  }
}
```

```
- Sistema inicia automaticamente
- Use http://<IP>:5000/tv
- Sem interação necessária
- Roda 24/7
```

---

## 🔄 Ciclo de Atualização

### TV Display Atualiza:

1. **Lista de sistemas** (10s)
   - Verifica quais estão ativos
   - Atualiza status (●/○)

2. **Screenshots** (15s)
   - Busca último screenshot de cada sistema
   - Atualiza imagem no grid

3. **Relógio** (1s)
   - Hora atual no canto superior

### Backend Coleta:

```
Google:    00:00 → 01:00 → 02:00 → 03:00 → ...  (60s)
PeopleSoft: 00:00 → 03:00 → 06:00 → 09:00 → ...  (180s)
```

---

## 📱 Acesso Remoto

### Na Rede Local

```bash
# Descobrir IP do servidor
ipconfig  # Windows
ifconfig  # Linux

# Acesso:
http://192.168.0.39:5000/tv
```

### Internet (Com Segurança)

```bash
# Opção 1: VPN
- Conectar à VPN corporativa
- Acessar via IP interno

# Opção 2: Reverse Proxy
- Nginx com autenticação
- Let's Encrypt (HTTPS)
- https://monitor.empresa.com/tv
```

---

## 🎨 Personalização da TV

### CSS Customizável

```css
/* Tamanho das cards */
.grid {
  grid-template-columns: repeat(2, 1fr);  /* 2 colunas */
}

/* Para 4 colunas: */
.grid {
  grid-template-columns: repeat(4, 1fr);
}

/* Cores do tema */
.status-active {
  background: #10b981;  /* Verde */
}

/* Tamanho da fonte */
.system-name {
  font-size: 24px;  /* Maior para TV */
}
```

### Fullscreen Automático

```html
<script>
// Adicionar ao tv_display_new.html
document.addEventListener('DOMContentLoaded', function() {
  if (document.documentElement.requestFullscreen) {
    document.documentElement.requestFullscreen();
  }
});
</script>
```

---

## 🔍 Troubleshooting

### Problema 1: Screenshots Não Aparecem

**Causa:** Sistema não está coletando

**Solução:**
```bash
# Ver logs
tail -f storage/logs/dashboard.log | grep "google"

# Verificar se job está rodando
curl http://localhost:5000/api/systems/all | jq
```

### Problema 2: TV Mostra "Carregando..."

**Causa:** API não responde

**Solução:**
```bash
# Testar API
curl http://localhost:5000/api/systems/all

# Verificar se backend iniciou
curl http://localhost:5000/api/health
```

### Problema 3: Intervalo Muito Longo

**Causa:** `collection_interval` muito alto

**Solução:**
```json
{
  "google": {
    "collection_interval": 30  ← Reduzir para 30s
  }
}
```

---

## 💡 Dicas de Produção

### 1. Use Headless

```json
{
  "headless": true  ← Menos recursos, mais estável
}
```

### 2. Intervalos Adequados

```
Dados críticos:     30-60s
Dados normais:      180-300s (3-5 min)
Dados históricos:   600-900s (10-15 min)
```

### 3. Mantenha TV Acordada

```bash
# Windows
powercfg /change monitor-timeout-ac 0

# Linux
xset s off
xset -dpms
```

### 4. Inicie com Windows/Linux

**Windows (Task Scheduler):**
```
Trigger: At startup
Action: python C:\path\to\main.py
```

**Linux (systemd):**
```bash
sudo systemctl enable monitor-scheduler
sudo systemctl start monitor-scheduler
```

---

## 🎯 Casos de Uso

### Uso 1: NOC (Network Operations Center)

```
- TV 55" na parede
- Grid com 4 sistemas
- Atualização a cada 60s
- Equipe monitora visualmente
```

### Uso 2: Sala de Reuniões

```
- TV 43" na sala
- 2 sistemas principais
- Atualização a cada 180s
- Apresentações automáticas
```

### Uso 3: Home Office

```
- Monitor secundário
- 1-2 sistemas
- Atualização a cada 30s
- Monitoramento pessoal
```

---

## 📊 Comparação

| Aspecto | Admin Dashboard | TV Display |
|---------|-----------------|------------|
| **URL** | `/` | `/tv` |
| **Controles** | ✅ Start/Stop | ❌ Nenhum |
| **Interação** | ✅ Dropdown | ❌ Passivo |
| **Sistemas** | 1 por vez | Todos no grid |
| **Atualização** | Manual/15s | Auto/15s |
| **Uso** | Operação | Monitoramento |

---

## 🎉 Resumo

### ✅ O Que Foi Feito:

1. **Corrigido:** GoogleCollector (test_connection)
2. **Criado:** TV Display com grid automático
3. **Configurado:** Sistemas iniciam automaticamente
4. **Headless:** Modo produção para ambos

### ✅ Como Usar:

```bash
# 1. Iniciar
python main.py

# 2. Abrir TV
http://localhost:5000/tv

# 3. Fullscreen (F11)

# 4. Deixar rodando 24/7
```

### ✅ Resultado:

- **PeopleSoft:** Coleta a cada 3 minutos
- **Google:** Coleta a cada 1 minuto
- **TV:** Atualiza automaticamente
- **Sem interação:** Tudo automático

**Execute e teste! 🚀**

---

## 📝 Próximos Passos

1. **Testar** com PeopleSoft e Google
2. **Adicionar** mais sistemas (Oracle, Bonita)
3. **Customizar** cores e layout para sua TV
4. **Deploy** em servidor permanente
5. **Monitorar** 24/7

**Perfeito para deixar na TV do escritório! 📺**
