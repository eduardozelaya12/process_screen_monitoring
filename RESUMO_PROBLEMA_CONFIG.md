# 🔴 PROBLEMA: Config Errado!

## ❌ O que estava acontecendo

```
Você editou:     config/config.yaml        ← YAML
Sistema lê:      config/systems_config.json ← JSON  ⚠️ DIFERENTE!
```

**Resultado:** Suas configurações eram ignoradas! ❌

---

## 📊 Evidências

### Logs mostravam valores ERRADOS:

```bash
# Você configurou no YAML:
collection_interval: 180  # 3 minutos

# Mas o log mostrava:
✓ Job agendado: peoplesoft a cada 300s  ← 5 minutos!
```

```bash
# Você configurou no YAML:
filters:
  user_id: "MBENITEZ"
  process_name: "AJ_BU_PS_CLI"

# Mas o log mostrava:
📋 FILTROS CONFIGURADOS:
============================================================
============================================================  ← VAZIO!
```

---

## ✅ SOLUÇÃO

Atualizei o arquivo **CORRETO**: `config/systems_config.json`

```json
{
  "peoplesoft": {
    "collection_interval": 180,  ← 3 minutos ✅
    "filters": {
      "user_id": "MBENITEZ",
      "process_name": "AJ_BU_PS_CLI",
      "time_filter": {
        "type": "0",
        "value": "70",
        "unit": "1"
      }
    }
  }
}
```

---

## 🚀 Teste Agora

```bash
python main.py
```

### Logs Corretos Esperados:

```
✓ Job agendado: peoplesoft a cada 180s    ← 180s agora! ✅

📋 FILTROS CONFIGURADOS:
  • User ID: MBENITEZ                     ← Filtros aparecem! ✅
  • Process Name: AJ_BU_PS_CLI
  • Time Filter:
    - Type: Last
    - Value: 70
    - Unit: Days

Buscando User ID: 'MBENITEZ'
✓ User ID 'MBENITEZ' selecionado          ← Filtro aplicado! ✅

Buscando Process Name: 'AJ_BU_PS_CLI'
✓ Process Name 'AJ_BU_PS_CLI' selecionado ← Filtro aplicado! ✅

✓ Filtros aplicados com sucesso
✓ Métricas extraídas: X processos
```

---

## 📝 Como Editar Filtros Agora

**Arquivo:** `config/systems_config.json` (JSON, não YAML!)

```json
{
  "peoplesoft": {
    "filters": {
      "user_id": "OUTRO_USUARIO",     ← Edite aqui
      "process_name": "OUTRO_PROCESSO",
      "run_status": "9",
      "time_filter": {
        "value": "30"                 ← Mudar dias
      }
    }
  }
}
```

---

## 🎯 Resumo

| Item | Antes | Depois |
|------|-------|--------|
| **Arquivo editado** | config.yaml ❌ | systems_config.json ✅ |
| **Intervalo** | 300s (ignorado) | 180s (lido) ✅ |
| **Filtros** | Vazios | Configurados ✅ |
| **Logs** | Sem filtros | Com filtros ✅ |

**Problema resolvido! Execute e veja os filtros sendo aplicados! 🚀**
