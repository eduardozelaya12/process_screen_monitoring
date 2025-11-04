# 🔧 CORREÇÃO: Config JSON vs YAML

## 🔴 PROBLEMA IDENTIFICADO

### O sistema estava usando o arquivo ERRADO!

**Você editou:** `config/config.yaml` ✅ (YAML)  
**Sistema lê:** `config/systems_config.json` ❌ (JSON)

---

## 📊 Evidências nos Logs

### 1. Intervalo Errado
```
INFO - ✓ Job agendado: peoplesoft a cada 300s
                                          ^^^ 300s (5 min)
```

**config.yaml tinha:** `collection_interval: 180` (3 min)  
**Mas o sistema usou:** 300s (padrão do JSON)

### 2. Filtros Vazios
```
INFO - ============================================================
INFO - 📋 FILTROS CONFIGURADOS:
INFO - ============================================================
INFO - ============================================================  ← VAZIO!
INFO - 🔍 Aplicando filtros...
```

**config.yaml tinha:**
```yaml
filters:
  user_id: "MBENITEZ"
  process_name: "AJ_BU_PS_CLI"
  ...
```

**Mas os logs mostram:** Nenhum filtro!

---

## 🔍 Análise do Código

### Orquestrador usa JSON

```python
# orchestrator/orchestrator.py linha 46
def __init__(self, config_path="config/systems_config.json"):
    self.config_path = config_path
    self.config = self._load_config()
```

### Todos os arquivos apontam para JSON

```python
# test_peoplesoft.py
with open('config/systems_config.json', 'r') as f:
    config = json.load(f)

# backend/routes.py
with open('config/systems_config.json', 'r') as f:
    systems = json.load(f)
```

---

## ✅ SOLUÇÃO APLICADA

### Atualizei `config/systems_config.json`

**ANTES (Formato Errado):**
```json
{
  "peoplesoft": {
    "collection_interval": 300,
    "filters": {
      "status": ["error", "warning"],  ← Formato antigo
      "last_hours": 24
    }
  }
}
```

**DEPOIS (Formato Correto):**
```json
{
  "peoplesoft": {
    "collection_interval": 180,  ✅ 3 minutos
    "filters": {
      "user_id": "MBENITEZ",         ✅ Formato novo
      "process_name": "AJ_BU_PS_CLI",
      "server": null,
      "run_status": null,
      "type": null,
      "dist_status": null,
      "instance_from": null,
      "instance_to": null,
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

## 📝 Estrutura Completa do JSON

### `config/systems_config.json`

```json
{
  "peoplesoft": {
    "enabled": true,
    "type": "selenium",
    "name": "PeopleSoft",
    "base_url": "http://pswebt1.ajover.com:8080/psp/erptest/EMPLOYEE/ERP",
    "process_monitor_url": "http://pswebt1.ajover.com:8080/psp/erptest/EMPLOYEE/ERP/c/PROCESSMONITOR.PROCESSMONITOR.GBL?FolderPath=PORTAL_ROOT_OBJECT.PT_PEOPLETOOLS.PT_PROCESS_SCHEDULER.PT_PROCESSMONITOR_GBL&IsFolder=false&IgnoreParamTempl=FolderPath%2cIsFolder",
    
    "credentials": {
      "username": "MBENITEZ",
      "password": "Ajover#2017"
    },
    
    "collection_interval": 180,
    
    "filters": {
      "user_id": "MBENITEZ",
      "process_name": "AJ_BU_PS_CLI",
      "server": null,
      "run_status": null,
      "type": null,
      "dist_status": null,
      "instance_from": null,
      "instance_to": null,
      "time_filter": {
        "type": "0",
        "value": "70",
        "unit": "1"
      }
    },
    
    "retry_attempts": 3,
    "timeout": 30
  },
  
  "oracle_fusion": {
    "enabled": false,
    ...
  },
  
  "bonita": {
    "enabled": false,
    ...
  },
  
  "n8n": {
    "enabled": false,
    ...
  }
}
```

---

## 🎯 Diferenças JSON vs YAML

| Aspecto | JSON | YAML |
|---------|------|------|
| **Extensão** | `.json` | `.yaml` ou `.yml` |
| **Sintaxe** | `{"key": "value"}` | `key: value` |
| **Comentários** | ❌ Não suporta | ✅ `# comentário` |
| **null** | `null` | `null` ou vazio |
| **Usado pelo sistema** | ✅ Sim | ❌ Não |

---

## 📊 Como Editar os Filtros

### Opção 1: Via JSON (Recomendado)

Edite `config/systems_config.json`:

```json
{
  "peoplesoft": {
    "filters": {
      "user_id": "OUTRO_USUARIO",     ← Mudar aqui
      "process_name": "OUTRO_PROCESSO",
      "run_status": "9",              ← Adicionar filtro
      "time_filter": {
        "value": "30"                 ← Mudar de 70 para 30 dias
      }
    }
  }
}
```

### Opção 2: Remover Filtros Específicos

```json
{
  "peoplesoft": {
    "filters": {
      "user_id": "MBENITEZ",
      "process_name": null,  ← Remove filtro de Process Name
      "server": null,
      ...
    }
  }
}
```

### Opção 3: Sem Filtros

```json
{
  "peoplesoft": {
    "filters": {}  ← Objeto vazio = sem filtros
  }
}
```

---

## 🚀 Teste Agora

```bash
python main.py
```

### Logs Esperados Agora:

```
INFO - ✓ Job agendado: peoplesoft a cada 180s  ← 180s agora!
INFO - 📸 Coletando dados: PeopleSoft
INFO - 🔐 Fazendo login...
INFO - ✓ Login bem-sucedido
INFO - ✓ Switch para iframe ptifrmtgtframe
INFO - ============================================================
INFO - 📋 FILTROS CONFIGURADOS:
INFO - ============================================================
INFO -   • User ID: MBENITEZ              ← Filtros aparecem!
INFO -   • Process Name: AJ_BU_PS_CLI
INFO -   • Time Filter:
INFO -     - Type: Last
INFO -     - Value: 70
INFO -     - Unit: Days
INFO - ============================================================
INFO - 🔍 Aplicando filtros...
INFO - Buscando User ID: 'MBENITEZ'
INFO - ✓ User ID 'MBENITEZ' selecionado
INFO - Buscando Process Name: 'AJ_BU_PS_CLI'
INFO - ✓ Process Name 'AJ_BU_PS_CLI' selecionado
INFO - ✓ Filtros aplicados com sucesso
INFO - ✓ Métricas extraídas
```

---

## 📋 Checklist

- [x] Identificado que sistema usa JSON, não YAML
- [x] Atualizado `systems_config.json` com filtros corretos
- [x] Alterado intervalo de 300s para 180s
- [x] Estrutura de filtros compatível com collector
- [ ] **PRÓXIMO PASSO:** Testar execução

---

## 💡 Dica: Comparação com Teste

### test_peoplesoft.py

```python
# Usa o mesmo arquivo!
with open('config/systems_config.json', 'r') as f:
    config = json.load(f)

peoplesoft_config = config['peoplesoft']
```

Agora o **teste** e a **produção** usam a **mesma configuração**!

---

## 🎉 Resultado

✅ **Arquivo correto:** `systems_config.json` atualizado  
✅ **Intervalo correto:** 180 segundos (3 minutos)  
✅ **Filtros corretos:** Estrutura compatível com collector  
✅ **Logs detalhados:** Filtros serão exibidos  

**Execute e confirme que os filtros aparecem nos logs! 🚀**
