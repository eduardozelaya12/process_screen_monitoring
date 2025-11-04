# ⏱️ CONFIGURAÇÃO: Intervalo de Execução e Logs de Filtros

## 🎯 Mudanças Implementadas

### 1. ✅ Intervalo de Coleta Configurável

**Localização:** `config/config.yaml`

```yaml
systems:
  - name: "PeopleSoft - Production"
    type: "peoplesoft"
    
    # ⏱️ INTERVALO DE COLETA (em segundos)
    collection_interval: 180  # 3 minutos
    
    filters:
      user_id: "MBENITEZ"
      # ... outros filtros
```

---

### 2. ✅ Logs Detalhados dos Filtros

**Localização:** `collectors/peoplesoft_collector.py` → `_apply_filters()`

Agora mostra todos os filtros configurados antes de aplicá-los.

---

## ⏱️ Configuração do Intervalo

### Como Funciona

O orquestrador lê `collection_interval` do config:

```python
# orchestrator/orchestrator.py
interval = self.config[system_name].get('collection_interval', 300)
# Se não especificar, usa 300s (5 minutos) como padrão
```

### Exemplos de Configuração

```yaml
# A cada 3 minutos (180 segundos)
collection_interval: 180

# A cada 5 minutos (padrão)
collection_interval: 300

# A cada 1 minuto (para testes)
collection_interval: 60

# A cada 10 minutos
collection_interval: 600
```

---

## 📊 Logs de Filtros

### Exemplo de Saída

Quando os filtros são aplicados, você verá:

```
INFO - ============================================================
INFO - 📋 FILTROS CONFIGURADOS:
INFO - ============================================================
INFO -   • User ID: MBENITEZ
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
```

### Se Nenhum Filtro Configurado

```
INFO - 📋 Nenhum filtro configurado - processando todos os dados
```

---

## 🔧 Configuração Completa

### `config/config.yaml`

```yaml
systems:
  - name: "PeopleSoft - Production"
    type: "peoplesoft"
    base_url: "http://pswebt1.ajover.com:8080/psp/erptest/EMPLOYEE/ERP/"
    process_monitor_url: "http://pswebt1.ajover.com:8080/psc/erptest/EMPLOYEE/ERP/c/PROCESSMONITOR.PROCESSMONITOR.GBL"
    
    # ⏱️ Executa a cada 3 minutos
    collection_interval: 180
    
    # 📋 Filtros que serão logados e aplicados
    filters:
      user_id: "MBENITEZ"
      process_name: "AJ_BU_PS_CLI"
      server: null
      run_status: null
      type: null
      dist_status: null
      instance_from: null
      instance_to: null
      time_filter:
        type: "0"    # Last
        value: "70"
        unit: "1"    # Days
    
    credentials:
      username: "MBENITEZ"
      password: "Ajover#2017"
```

---

## 📝 Logs Completos de Execução

### Execução Típica (a cada 3 minutos)

```
2025-11-04 12:00:00 - INFO - 📸 Coletando dados: PeopleSoft - Production
2025-11-04 12:00:00 - INFO - ✓ WebDriver inicializado
2025-11-04 12:00:00 - INFO - 🔐 Fazendo login...
2025-11-04 12:00:05 - INFO - ✓ Login bem-sucedido
2025-11-04 12:00:05 - INFO - Navegando para: http://pswebt1.ajover.com:8080/psc/erptest/...
2025-11-04 12:00:09 - INFO - ✓ Switch para iframe ptifrmtgtframe (por NAME)
2025-11-04 12:00:11 - INFO - ============================================================
2025-11-04 12:00:11 - INFO - 📋 FILTROS CONFIGURADOS:
2025-11-04 12:00:11 - INFO - ============================================================
2025-11-04 12:00:11 - INFO -   • User ID: MBENITEZ
2025-11-04 12:00:11 - INFO -   • Process Name: AJ_BU_PS_CLI
2025-11-04 12:00:11 - INFO -   • Time Filter:
2025-11-04 12:00:11 - INFO -     - Type: Last
2025-11-04 12:00:11 - INFO -     - Value: 70
2025-11-04 12:00:11 - INFO -     - Unit: Days
2025-11-04 12:00:11 - INFO - ============================================================
2025-11-04 12:00:11 - INFO - 🔍 Aplicando filtros...
2025-11-04 12:00:11 - INFO - Buscando User ID: 'MBENITEZ'
2025-11-04 12:00:15 - INFO - ✓ User ID 'MBENITEZ' selecionado
2025-11-04 12:00:15 - INFO - Buscando Process Name: 'AJ_BU_PS_CLI'
2025-11-04 12:00:20 - INFO - ✓ Process Name 'AJ_BU_PS_CLI' selecionado
2025-11-04 12:00:24 - INFO - ✓ Filtros aplicados com sucesso
2025-11-04 12:00:26 - INFO - ✓ Métricas extraídas: 12 processos, 0 erros, 100.00% sucesso
2025-11-04 12:00:26 - INFO - ✓ Screenshot salvo: storage/screenshots/peoplesoft/screenshot_20251104_120026.png

# Aguarda 3 minutos...

2025-11-04 12:03:00 - INFO - 📸 Coletando dados: PeopleSoft - Production
# ... repete o processo
```

---

## 🎨 Personalização dos Logs

### Logs Mostram Valores Legíveis

| Filtro | Valor no Config | Log Exibido |
|--------|----------------|-------------|
| **Time Filter Type** | `"0"` | `Type: Last` |
| **Time Filter Type** | `"1"` | `Type: Date Range` |
| **Time Filter Unit** | `"0"` | `Unit: All` |
| **Time Filter Unit** | `"1"` | `Unit: Days` |
| **Time Filter Unit** | `"2"` | `Unit: Hours` |
| **Time Filter Unit** | `"3"` | `Unit: Minutes` |
| **Time Filter Unit** | `"4"` | `Unit: Years` |

---

## 📊 Exemplos de Configuração

### Exemplo 1: Monitoramento Rápido (1 minuto)

```yaml
systems:
  - name: "PeopleSoft - Dev"
    collection_interval: 60  # 1 minuto
    filters:
      run_status: "3"  # Apenas erros
```

**Logs:**
```
INFO - ✓ Job agendado: PeopleSoft - Dev a cada 60s
INFO - 📋 FILTROS CONFIGURADOS:
INFO -   • Run Status: 3
```

---

### Exemplo 2: Monitoramento Normal (3 minutos)

```yaml
systems:
  - name: "PeopleSoft - Production"
    collection_interval: 180  # 3 minutos
    filters:
      user_id: "MBENITEZ"
      process_name: "AJ_BU_PS_CLI"
```

**Logs:**
```
INFO - ✓ Job agendado: PeopleSoft - Production a cada 180s
INFO - 📋 FILTROS CONFIGURADOS:
INFO -   • User ID: MBENITEZ
INFO -   • Process Name: AJ_BU_PS_CLI
```

---

### Exemplo 3: Monitoramento Leve (10 minutos)

```yaml
systems:
  - name: "PeopleSoft - Background"
    collection_interval: 600  # 10 minutos
    filters: {}  # Sem filtros
```

**Logs:**
```
INFO - ✓ Job agendado: PeopleSoft - Background a cada 600s
INFO - 📋 Nenhum filtro configurado - processando todos os dados
```

---

## 🔍 Verificar Intervalo em Execução

### Logs de Inicialização

Quando o sistema inicia, você verá:

```
INFO - ✓ Job agendado: PeopleSoft - Production a cada 180s
                                                    ^^^ 
                                        Intervalo configurado
```

### Logs do Scheduler

```
INFO - Added job "Coleta PeopleSoft - Production" to job store "default"
INFO - Job "Coleta PeopleSoft - Production (trigger: interval[0:03:00], next run at: 2025-11-04 12:03:00)" executed successfully
                                                                  ^^^^^^
                                                            Próxima execução em 3 minutos
```

---

## ⚙️ Como Funciona Internamente

```python
# 1. Orquestrador lê o config
interval = self.config['PeopleSoft - Production'].get('collection_interval', 300)
# Resultado: interval = 180

# 2. Agenda job com intervalo
self.scheduler.add_job(
    trigger=IntervalTrigger(seconds=180),  # ← Intervalo de 3 minutos
    ...
)

# 3. Collector carrega filtros
self.filters = config.get('filters', {})

# 4. Logs detalhados antes de aplicar
logger.info("📋 FILTROS CONFIGURADOS:")
logger.info(f"  • User ID: {self.filters['user_id']}")
```

---

## 🎯 Benefícios

### ✅ Intervalo Configurável
- **Flexível:** Ajuste sem editar código
- **Por sistema:** Cada sistema pode ter intervalo diferente
- **Documentado:** Valor visível no config

### ✅ Logs Detalhados
- **Transparência:** Vê exatamente quais filtros estão ativos
- **Debug:** Fácil identificar configuração errada
- **Auditoria:** Histórico do que foi filtrado
- **Valores legíveis:** "Days" em vez de "1"

---

## 🚀 Teste Agora

```bash
python main.py
```

### Observe:

1. **No início:**
   ```
   INFO - ✓ Job agendado: PeopleSoft - Production a cada 180s
   ```

2. **A cada 3 minutos:**
   ```
   INFO - 📋 FILTROS CONFIGURADOS:
   INFO -   • User ID: MBENITEZ
   INFO -   • Process Name: AJ_BU_PS_CLI
   INFO -   • Time Filter: ...
   ```

3. **Próxima execução:**
   ```
   next run at: 2025-11-04 12:XX:00
   ```

---

## 📋 Resumo

| Configuração | Onde | Valor | Efeito |
|-------------|------|-------|--------|
| **Intervalo** | `config.yaml` | `180` | Executa a cada 3 minutos |
| **Logs** | `_apply_filters()` | Automático | Mostra filtros antes de aplicar |
| **Padrão** | Se omitir | `300s` | Executa a cada 5 minutos |

---

## 🎉 Pronto!

✅ **Intervalo configurado:** 3 minutos (180 segundos)  
✅ **Logs detalhados:** Filtros exibidos claramente  
✅ **Valores legíveis:** "Days" em vez de códigos  
✅ **Fácil debug:** Vê exatamente o que está configurado  

**Execute e veja funcionando! 🚀**
