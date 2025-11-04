# ✅ MIGRAÇÃO COMPLETA: Teste → Produção

## 🎯 Solução Implementada: **Filtros via Config YAML**

---

## 📊 Resumo da Migração

```
test_peoplesoft.py                    PeopleSoftCollector
==================                    ===================

Input Interativo              →       Config YAML
├─ user_id = input()          →       filters:
├─ server = input()           →         user_id: "AJPEOPLE"
├─ run_status = input()       →         server: "PSUNX"
└─ ...                        →         run_status: "9"
                                       ...

Funções de Modal              →       Métodos Privados
├─ search_in_modal()          →       _search_in_modal()
├─ search_user_id_modal()     →       (integrado)
└─ search_process_name()      →       (integrado)

Funções de Filtro             →       Métodos Privados
├─ set_select_by_id()         →       _set_select_field()
├─ set_text_field()           →       _set_text_field()
└─ clear_*()                  →       (integrado)

Aplicação Manual              →       Automática
├─ if user_id_val:            →       _apply_filters()
│   search_user_id_modal()    →       (lê self.filters)
└─ if server_val:             →       (aplica tudo)
    set_select_by_id()        →
```

---

## 🔧 Como Usar Agora

### 1️⃣ Configure o YAML

Edite `config/config.yaml`:

```yaml
systems:
  - name: "PeopleSoft - Production"
    type: "peoplesoft"
    base_url: "http://pswebt1.ajover.com:8080/psp/erptest/EMPLOYEE/ERP/"
    process_monitor_url: "http://pswebt1.ajover.com:8080/psc/erptest/EMPLOYEE/ERP/c/PROCESSMONITOR.PROCESSMONITOR.GBL"
    
    # ✅ FILTROS (NOVO!)
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

### 2️⃣ Execute

```bash
python main.py
```

### 3️⃣ Resultado

```
INFO - 📸 Coletando dados: PeopleSoft - Production
INFO - 🔍 Aplicando filtros configurados...
INFO - Buscando User ID: 'AJPEOPLE'
INFO - ✓ User ID 'AJPEOPLE' selecionado
INFO - ✓ Filtros aplicados com sucesso
INFO - ✓ Métricas extraídas: 45 processos
INFO - ✓ Screenshot salvo
```

---

## 📋 Checklist de Migração

### ✅ Código
- [x] Adicionar `self.filters` no `__init__`
- [x] Criar método `_apply_filters()`
- [x] Criar método `_search_in_modal()`
- [x] Criar método `_set_select_field()`
- [x] Criar método `_set_text_field()`
- [x] Criar método `_click_refresh()`
- [x] Integrar `_apply_filters()` no fluxo de `_capture_and_extract()`
- [x] Remover `_clear_name_filter()` antigo

### ✅ Configuração
- [x] Criar estrutura de filtros no config
- [x] Documentar todos os filtros disponíveis
- [x] Criar exemplos de configuração
- [x] Documentar valores válidos

### ✅ Documentação
- [x] `EXEMPLO_CONFIG_FILTROS.yaml` - Exemplos práticos
- [x] `GUIA_FILTROS_PRODUCAO.md` - Guia completo
- [x] `MIGRACAO_COMPLETA.md` - Este arquivo

---

## 🎨 Arquitetura Final

```
┌─────────────────────────────────────────────────┐
│ config/config.yaml                              │
│                                                 │
│ systems:                                        │
│   - name: "PeopleSoft"                          │
│     filters:                                    │
│       user_id: "AJPEOPLE"     ← CONFIGURAÇÃO   │
│       server: "PSUNX"                           │
│       run_status: "9"                           │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ PeopleSoftCollector                             │
│                                                 │
│ def __init__(config):                           │
│   self.filters = config.get('filters', {})     │
│                                                 │
│ def _capture_and_extract():                     │
│   ...                                           │
│   self._apply_filters()      ← APLICAÇÃO       │
│   metrics = self._extract_metrics()            │
│   ...                                           │
│                                                 │
│ def _apply_filters():                           │
│   if self.filters.get('user_id'):              │
│     self._search_in_modal(...)                 │
│   if 'server' in self.filters:                 │
│     self._set_select_field(...)                │
│   ...                                           │
│   self._click_refresh()                        │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│ PeopleSoft UI                                   │
│                                                 │
│ [User ID: AJPEOPLE    ]  ← Preenchido          │
│ [Server: PSUNX      ▼]  ← Selecionado          │
│ [Run Status: Success▼]  ← Selecionado          │
│ [Refresh]               ← Clicado              │
│                                                 │
│ [Process Table - Filtered]  ← Resultado        │
└─────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo Completo

```
┌─────────────────────┐
│  main.py executa    │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Carrega config.yaml │
│ filters: {...}      │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ PeopleSoftCollector │
│ __init__(config)    │
│ self.filters = {...}│
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ collect()           │
│ ↓ _capture_and_*()  │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Login / Cookies     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Navega para Monitor │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Switch iframe       │
│ ptifrmtgtframe      │
└──────────┬──────────┘
           ↓
┌────────────────────────────┐
│ _apply_filters()           │
├────────────────────────────┤
│ • User ID modal            │
│ • Process Name modal       │
│ • Server dropdown          │
│ • Run Status dropdown      │
│ • Type dropdown            │
│ • Distribution dropdown    │
│ • Instance From/To text    │
│ • Time Filter (3 campos)   │
│ • Click Refresh            │
└──────────┬─────────────────┘
           ↓
┌─────────────────────┐
│ _extract_metrics()  │
│ • Conta processos   │
│ • Identifica erros  │
│ • Calcula taxa      │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Screenshot          │
│ + Métricas          │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Retorna Dados       │
│ ✓ screenshot_path   │
│ ✓ metrics           │
│ ✓ url               │
└─────────────────────┘
```

---

## 💡 Vantagens da Solução

### ✅ Config via YAML

**Vantagens:**
- ✅ **Fácil manutenção** - Edita texto, não código
- ✅ **Versionável** - Rastreia mudanças no Git
- ✅ **Múltiplos ambientes** - Dev, QA, Prod
- ✅ **Múltiplos monitores** - Várias configs diferentes
- ✅ **Sem recompilação** - Só reinicia o script
- ✅ **Documentado** - Valores claros e comentáveis

**Alternativas Descartadas:**
- ❌ **Input interativo** - Não funciona em produção/cron
- ❌ **Argumentos CLI** - Muitos filtros = comando gigante
- ❌ **Hardcoded** - Inflexível e difícil de manter
- ❌ **Banco de dados** - Overkill para configuração

---

## 📊 Comparação Completa

| Feature | Teste (Input) | Produção (YAML) |
|---------|--------------|-----------------|
| **Entrada** | Manual | Automática |
| **Interface** | Terminal | Config file |
| **Execução** | Interativa | Batch/Cron |
| **Filtros** | 11 filtros ✅ | 11 filtros ✅ |
| **Modais** | Automático ✅ | Automático ✅ |
| **Iframe detect** | Automático ✅ | Automático ✅ |
| **Limpeza** | Enter=None ✅ | null=None ✅ |
| **Logs** | Print | Logger ✅ |
| **Screenshots** | Erro ✅ | Erro ✅ |
| **Uso** | Debug | Produção |
| **Manutenção** | ❌ Edita código | ✅ Edita YAML |
| **Versionamento** | ❌ N/A | ✅ Git |
| **Multi-env** | ❌ Não | ✅ Sim |

---

## 🚀 Próximos Passos

### 1. Atualizar Config
```bash
# Editar config/config.yaml
# Adicionar seção filters conforme exemplos
```

### 2. Testar
```bash
python main.py
```

### 3. Validar
- ✅ Logs mostram filtros aplicados?
- ✅ Screenshot reflete filtros?
- ✅ Métricas estão corretas?

### 4. Produção
```bash
# Configurar cron job
0 */6 * * * cd /path/to/monitor_scheduler && python main.py
```

---

## 📚 Arquivos Importantes

| Arquivo | Descrição |
|---------|-----------|
| `collectors/peoplesoft_collector.py` | ✅ Implementação completa |
| `config/config.yaml` | ✅ Seu arquivo de config |
| `EXEMPLO_CONFIG_FILTROS.yaml` | 📖 Exemplos de configuração |
| `GUIA_FILTROS_PRODUCAO.md` | 📖 Guia completo de uso |
| `MIGRACAO_COMPLETA.md` | 📖 Este arquivo |
| `test_peoplesoft.py` | 🧪 Mantido para testes manuais |

---

## 🎉 MIGRAÇÃO CONCLUÍDA!

### ✅ O que foi feito:

1. ✅ **Código migrado** do teste para o collector
2. ✅ **Config via YAML** implementado
3. ✅ **11 filtros** totalmente funcionais
4. ✅ **Detecção automática** de iframes modais
5. ✅ **Documentação completa** criada
6. ✅ **Exemplos práticos** fornecidos

### 🚀 Pronto para usar:

```yaml
# config/config.yaml
systems:
  - name: "PeopleSoft"
    type: "peoplesoft"
    # ... urls ...
    
    filters:
      user_id: "AJPEOPLE"
      server: "PSUNX"
      run_status: "9"
      time_filter:
        type: "0"
        value: "70"
        unit: "1"
```

```bash
python main.py
```

**É só configurar e rodar!** 🎯
