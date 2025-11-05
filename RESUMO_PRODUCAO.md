# 🚀 RESUMO: Headless e Produção

## ✅ RESPOSTA RÁPIDA

### 1. Screenshots funcionam em headless?

**SIM!** Screenshots são salvos **independente** do modo:

```python
driver.save_screenshot("antes_refresh.png")  ✅ Funciona em headless
driver.save_screenshot("highlight_refresh.png")  ✅ Funciona em headless
driver.save_screenshot("depois_refresh.png")  ✅ Funciona em headless
```

**Você NÃO precisa ver a janela para ter os screenshots!**

---

### 2. Como mudar entre Visual e Headless?

**Arquivo:** `config/systems_config.json`

```json
{
  "peoplesoft": {
    "headless": false,  ← Mude aqui: false = Visual, true = Headless
    "collection_interval": 180,
    "filters": {...}
  }
}
```

Depois de mudar, reinicie:
```bash
Ctrl+C  (parar)
python main.py  (iniciar)
```

---

## 🎯 Quando Usar Cada Modo

### 👀 Visual (`headless: false`)

**Use para:**
- ✅ Debug (ver o que está acontecendo)
- ✅ Ver highlight vermelho+amarelo
- ✅ Testar filtros novos
- ✅ Desenvolvimento local

**Logs:**
```
👀 Modo VISUAL ativado (com interface)
```

---

### 🎭 Headless (`headless: true`)

**Use para:**
- ✅ Produção
- ✅ Servidor sem interface gráfica
- ✅ Mais rápido (~20% menos tempo)
- ✅ Menos memória (~40% menos)
- ✅ Deploy em Docker/Linux

**Logs:**
```
🎭 Modo HEADLESS ativado (sem interface visual)
```

---

## 📋 Configuração Atual

### Debug Local (Agora):
```json
{
  "peoplesoft": {
    "headless": false,  ← Ver navegação
    "collection_interval": 180
  }
}
```

### Produção (Depois):
```json
{
  "peoplesoft": {
    "headless": true,  ← Sem janela
    "collection_interval": 180
  }
}
```

---

## 🔄 Workflow Recomendado

```
1. DESENVOLVIMENTO (Sua Máquina)
   ├─ headless: false  ← Ver navegação
   ├─ Testar filtros
   ├─ Ver highlight
   └─ Verificar screenshots

2. TESTE HEADLESS (Sua Máquina)
   ├─ headless: true  ← Modo produção
   ├─ Verificar logs
   ├─ Verificar screenshots salvos
   └─ Confirmar tudo funciona

3. DEPLOY (Servidor)
   ├─ headless: true  ← SEMPRE true
   ├─ Copiar arquivos
   ├─ Configurar cron/systemd
   └─ Monitorar logs
```

---

## 🎨 Interface Web (FUTURO)

Para mudar configuração sem editar JSON:

```
Dashboard
└── [⚙️ Configurações]
    └── Modal
        ├── 🎭 Modo Headless [Toggle ON/OFF]
        ├── ⏱️ Intervalo [Slider: 60s - 600s]
        ├── 📋 Filtros
        │   ├── User ID [Input]
        │   ├── Process Name [Input]
        │   └── ...
        └── [💾 Salvar e Aplicar]
```

**Isso será implementado na próxima versão!**

---

## 📊 Comparação

| Item | Visual | Headless |
|------|--------|----------|
| **Janela** | ✅ Abre Chrome | ❌ Sem janela |
| **Velocidade** | Normal | +20% rápido |
| **Memória** | 500MB | 300MB |
| **Screenshots** | ✅ Sim | ✅ Sim |
| **Highlight visível** | ✅ Sim | ❌ Não* |
| **Debug** | ✅ Fácil | ⚠️ Via logs |
| **Produção** | ❌ Não ideal | ✅ Ideal |

*Screenshot do highlight é salvo mesmo sem ver

---

## 🚀 Teste Agora

### 1. Teste Visual (Debug):
```json
{"headless": false}
```
```bash
python main.py
# Vê janela, vê highlight, vê navegação
```

### 2. Teste Headless (Produção):
```json
{"headless": true}
```
```bash
python main.py
# Sem janela, mas screenshots salvos em storage/logs/
```

---

## 📝 Checklist

Antes de produção:

- [ ] Testar com `headless: false` (debug)
- [ ] Testar com `headless: true` (produção)
- [ ] Verificar screenshots salvos em ambos
- [ ] Verificar logs corretos
- [ ] Verificar filtros aplicados
- [ ] Confirmar métricas extraídas

---

## 🎉 Resumo Final

✅ **Screenshots funcionam em headless!**  
✅ **Mude via JSON: `"headless": true/false`**  
✅ **Reinicie após mudar**  
✅ **Futuro: Interface web para configurar**  
✅ **Produção: SEMPRE `headless: true`**  

**Documentação completa em: `GUIA_PRODUCAO.md`** 📚
