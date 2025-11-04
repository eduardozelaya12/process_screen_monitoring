# 🎯 GUIA COMPLETO: Filtros em Produção - PeopleSoft Collector

## ✅ MIGRAÇÃO CONCLUÍDA!

A lógica de filtros do `test_peoplesoft.py` foi **completamente migrada** para o `PeopleSoftCollector`.

---

## 🔧 Como Funciona

### 📋 Configuração via YAML (Recomendado para Produção)

Os filtros são definidos no arquivo `config/config.yaml`:

```yaml
systems:
  - name: "PeopleSoft - Production"
    type: "peoplesoft"
    base_url: "http://pswebt1.ajover.com:8080/psp/erptest/EMPLOYEE/ERP/"
    process_monitor_url: "http://pswebt1.ajover.com:8080/psc/erptest/EMPLOYEE/ERP/c/PROCESSMONITOR.PROCESSMONITOR.GBL"
    
    # ✅ FILTROS CONFIGURADOS
    filters:
      user_id: "AJPEOPLE"          # Busca via modal
      process_name: null           # null = não filtrar
      server: "PSUNX"              # Dropdown
      run_status: "9"              # 9=Success
      type: null                   # null = qualquer tipo
      dist_status: null            # null = qualquer status
      instance_from: null          # Range de instances
      instance_to: null
      time_filter:                 # Filtro de tempo
        type: "0"                  # 0=Last
        value: "70"                # 70 unidades
        unit: "1"                  # 1=Days (últimos 70 dias)
    
    credentials:
      username: "seu_usuario"
      password: "sua_senha"
```

---

## 📊 Filtros Disponíveis

### 1. **User ID** (Modal)
- **Tipo:** Busca via modal automático
- **Exemplo:** `user_id: "AJPEOPLE"`
- **Limpar:** `user_id: null`

### 2. **Process Name** (Modal)
- **Tipo:** Busca via modal automático
- **Exemplo:** `process_name: "AJ_LDEXP"`
- **Limpar:** `process_name: null`

### 3. **Server** (Dropdown)
- **Tipo:** Dropdown select
- **Valores:** "PSUNX", "AJNODE4B", "AJNODE4C", etc.
- **Exemplo:** `server: "PSUNX"`
- **Limpar:** `server: null`

### 4. **Run Status** (Dropdown)
- **Tipo:** Dropdown select
- **Valores:**
  - `1` = Cancel
  - `3` = Error
  - `7` = Processing
  - `8` = Cancelled
  - `9` = Success
  - `10` = No Success
  - `17` = Warning
  - `18` = Blocked
- **Exemplo:** `run_status: "9"`  (apenas sucessos)
- **Limpar:** `run_status: null`

### 5. **Type** (Dropdown)
- **Tipo:** Dropdown select
- **Valores:** "Application Engine", "PSJob", "SQR Report", "Crystal", etc.
- **Exemplo:** `type: "Application Engine"`
- **Limpar:** `type: null`

### 6. **Distribution Status** (Dropdown)
- **Tipo:** Dropdown select
- **Valores:**
  - `2` = Processing
  - `3` = Generated
  - `4` = Not Posted
  - `5` = Posted
  - `9` = Pending
- **Exemplo:** `dist_status: "5"`
- **Limpar:** `dist_status: null`

### 7. **Instance Range** (Text Fields)
- **Tipo:** Campos de texto para números
- **Exemplo:**
  ```yaml
  instance_from: "7997100"
  instance_to: "7997200"
  ```
- **Limpar:** `instance_from: null` / `instance_to: null`

### 8. **Time Filter** (3 campos)
- **Tipo:** Combinação de dropdown + text + dropdown
- **Estrutura:**
  ```yaml
  time_filter:
    type: "0"   # 0=Last (padrão), 1=Date Range
    value: "70" # Número (quantidade)
    unit: "1"   # 0=All, 1=Days, 2=Hours, 3=Minutes, 4=Years
  ```
- **Exemplos:**
  ```yaml
  # Últimos 7 dias
  time_filter:
    type: "0"
    value: "7"
    unit: "1"
  
  # Últimas 24 horas
  time_filter:
    type: "0"
    value: "24"
    unit: "2"
  
  # Último ano
  time_filter:
    type: "0"
    value: "1"
    unit: "4"
  ```

---

## 🎨 Exemplos de Configuração

### Exemplo 1: Monitorar Erros Recentes
```yaml
systems:
  - name: "PeopleSoft - Erros 24h"
    type: "peoplesoft"
    # ... urls ...
    
    filters:
      run_status: "3"  # Apenas erros
      time_filter:
        type: "0"
        value: "24"
        unit: "2"  # Últimas 24 horas
```

### Exemplo 2: Processos de um Usuário Específico
```yaml
systems:
  - name: "PeopleSoft - User MBENITEZ"
    type: "peoplesoft"
    # ... urls ...
    
    filters:
      user_id: "MBENITEZ"
      server: "PSUNX"
      time_filter:
        type: "0"
        value: "7"
        unit: "1"  # Últimos 7 dias
```

### Exemplo 3: Processos Bem-Sucedidos Recentes
```yaml
systems:
  - name: "PeopleSoft - Success Only"
    type: "peoplesoft"
    # ... urls ...
    
    filters:
      run_status: "9"  # Success
      time_filter:
        type: "0"
        value: "3"
        unit: "1"  # Últimos 3 dias
```

### Exemplo 4: Sem Filtros (Todos os Processos)
```yaml
systems:
  - name: "PeopleSoft - Todos"
    type: "peoplesoft"
    # ... urls ...
    
    # Não incluir seção filters
    # OU
    filters: {}  # Vazio
```

---

## 🔄 Fluxo de Execução

```
1. Collector inicializado
   ↓
2. Carrega filtros do config.yaml
   self.filters = config.get('filters', {})
   ↓
3. Faz login/carrega cookies
   ↓
4. Navega para Process Monitor
   ↓
5. Switch para iframe ptifrmtgtframe
   ↓
6. Aplica filtros (se configurados)
   - User ID → _search_in_modal()
   - Process Name → _search_in_modal()
   - Server → _set_select_field()
   - Run Status → _set_select_field()
   - Type → _set_select_field()
   - Distribution Status → _set_select_field()
   - Instance From/To → _set_text_field()
   - Time Filter → _set_select_field() + _set_text_field()
   - Refresh → _click_refresh()
   ↓
7. Extrai métricas da tabela filtrada
   ↓
8. Salva screenshot
   ↓
9. Retorna dados
```

---

## 🛠️ Métodos Implementados

### `_apply_filters()`
- Aplica todos os filtros configurados em `self.filters`
- Chama automaticamente os métodos específicos para cada tipo

### `_search_in_modal(search_value, modal_type, prompt_id, search_field_id)`
- Busca em modais com detecção automática de iframe (ptModFrame_X)
- Usado para: User ID e Process Name
- **Features:**
  - ✅ Detecção automática de iframe (0-9)
  - ✅ Busca automática ou Look Up
  - ✅ Múltiplos seletores de resultado
  - ✅ Volta ao iframe principal automaticamente
  - ✅ Screenshot de erro automático

### `_set_select_field(field_id, value, field_name)`
- Define valor em dropdown ou limpa se `None`
- Usado para: Server, Run Status, Type, Distribution Status, Time Filter Type/Unit
- **Features:**
  - ✅ Tenta por value primeiro
  - ✅ Fallback para visible text
  - ✅ Limpa se valor for None

### `_set_text_field(field_id, value, field_name)`
- Define valor em campo de texto ou limpa se `None`
- Usado para: Instance From/To, Time Filter Value
- **Features:**
  - ✅ Limpa campo sempre
  - ✅ Preenche se valor não for None

### `_click_refresh()`
- Clica no botão Refresh após aplicar filtros
- **Features:**
  - ✅ Múltiplos seletores (ID, XPath)
  - ✅ JavaScript click (evita overlay)
  - ✅ Aguarda atualização (4s)

---

## 📝 Logs Esperados

### ✅ Com Filtros Configurados
```
INFO - 📸 Coletando dados: PeopleSoft - Production
INFO - ✓ Cookies carregados
INFO - Navegando para: http://...
INFO - ✓ Switch para iframe 'ptifrmtgtframe' realizado com sucesso
INFO - 🔍 Aplicando filtros configurados...
INFO - Buscando User ID: 'AJPEOPLE'
DEBUG - Modal encontrado em ptModFrame_0
INFO - ✓ User ID 'AJPEOPLE' selecionado
DEBUG - Server = 'PSUNX'
DEBUG - Run Status = '9'
DEBUG - Time Filter Type = '0'
DEBUG - Time Filter Value = '70'
DEBUG - Time Filter Unit = '1'
INFO - Clicando em Refresh...
INFO - ✓ Refresh clicado, aguardando atualização...
INFO - ✓ Filtros aplicados com sucesso
INFO - ✓ Métricas extraídas: 45 processos, 2 erros, 95.56% sucesso
INFO - ✓ Screenshot salvo: storage/screenshots/peoplesoft/screenshot_20251104_121530.png
```

### ✅ Sem Filtros
```
INFO - 📸 Coletando dados: PeopleSoft - Todos
INFO - ✓ Cookies carregados
INFO - Navegando para: http://...
INFO - ✓ Switch para iframe 'ptifrmtgtframe' realizado com sucesso
INFO - Nenhum filtro configurado, pulando aplicação
INFO - ✓ Métricas extraídas: 150 processos, 5 erros, 96.67% sucesso
INFO - ✓ Screenshot salvo: storage/screenshots/peoplesoft/screenshot_20251104_121530.png
```

---

## 🚀 Como Testar

### 1. Atualizar Config
Edite `config/config.yaml`:
```yaml
systems:
  - name: "PeopleSoft - Teste Filtros"
    type: "peoplesoft"
    base_url: "http://pswebt1.ajover.com:8080/psp/erptest/EMPLOYEE/ERP/"
    process_monitor_url: "http://pswebt1.ajover.com:8080/psc/erptest/EMPLOYEE/ERP/c/PROCESSMONITOR.PROCESSMONITOR.GBL"
    
    filters:
      user_id: "AJPEOPLE"
      server: "PSUNX"
      run_status: "9"
      time_filter:
        type: "0"
        value: "70"
        unit: "1"
    
    credentials:
      username: "seu_usuario"
      password: "sua_senha"
```

### 2. Executar Coleta
```bash
python main.py
```

### 3. Verificar Logs
- Verifique se filtros foram aplicados
- Verifique screenshot em `storage/screenshots/peoplesoft/`
- Verifique métricas extraídas

---

## 🎯 Comparação: Teste vs Produção

| Aspecto | test_peoplesoft.py | PeopleSoftCollector |
|---------|-------------------|---------------------|
| **Entrada de filtros** | Input interativo | Config YAML |
| **Detecção iframe modal** | ✅ Automática | ✅ Automática |
| **Busca em modais** | ✅ User ID + Process Name | ✅ User ID + Process Name |
| **Limpeza de campos** | ✅ Enter = None | ✅ null = None |
| **Todos os filtros** | ✅ 11 filtros | ✅ 11 filtros |
| **Logs** | ✅ Print verboso | ✅ Logger profissional |
| **Screenshots erro** | ✅ Automático | ✅ Automático |
| **Uso** | 🧪 Teste manual | 🚀 Produção automatizada |

---

## 💡 Dicas

### ✅ Para Diferentes Ambientes
```yaml
# Desenvolvimento - Mais dados
filters:
  time_filter:
    value: "90"  # 90 dias

# Produção - Apenas recente
filters:
  time_filter:
    value: "7"  # 7 dias
```

### ✅ Para Múltiplos Monitores
```yaml
systems:
  - name: "PeopleSoft - Erros"
    filters:
      run_status: "3"
  
  - name: "PeopleSoft - Sucessos"
    filters:
      run_status: "9"
  
  - name: "PeopleSoft - Todos"
    filters: {}
```

### ✅ Para Alertas Específicos
```yaml
# Monitor apenas processos críticos de um usuário
filters:
  user_id: "SYSTEM_USER"
  process_name: "CRITICAL_JOB"
  run_status: null  # Qualquer status
```

---

## 🎉 PRONTO PARA PRODUÇÃO!

✅ **Filtros migrados** do teste para produção  
✅ **Config via YAML** para fácil manutenção  
✅ **Detecção automática** de iframes modais  
✅ **11 filtros completos** implementados  
✅ **Logs profissionais** com logger  
✅ **Screenshots automáticos** em caso de erro  
✅ **Reutilização** do código testado  

**Basta configurar o YAML e executar!** 🚀

---

## 📚 Arquivos Relacionados

- `collectors/peoplesoft_collector.py` - Implementação completa
- `EXEMPLO_CONFIG_FILTROS.yaml` - Exemplos de configuração
- `test_peoplesoft.py` - Teste original (mantido para debug)
- `config/config.yaml` - Seu arquivo de configuração
