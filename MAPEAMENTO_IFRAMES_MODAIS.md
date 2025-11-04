# 🗺️ MAPEAMENTO COMPLETO DE IFRAMES - PeopleSoft Process Monitor

## 🎯 Estrutura de Iframes

### Iframe Principal
```
ptifrmtgtframe (ou TargetContent)
├─ Filtros da página principal
├─ Botões Refresh
├─ Tabela de processos
└─ Lupas que abrem modais
```

### Iframes de Modais
```
Cada modal abre em seu próprio iframe!

ptModFrame_0  → Modal genérico / primeiro modal
ptModFrame_1  → User ID modal       ← MAPEADO! ✅
ptModFrame_2  → Process Name modal  ← MAPEADO! ✅
ptModFrame_3  → Outros modais...
ptModFrame_4  → Outros modais...
```

---

## 📋 Mapeamento Detalhado

### 1. **User ID Modal** (ptModFrame_1) ✅

```python
Modal Type: User ID
Iframe: ptModFrame_1
Lupa ID: PMN_FILTER_WRK_WS_OPRID$prompt
Campo ID: PMN_OPRID_VW_OPRID
```

**Uso:**
```python
search_user_id_modal("MBENITEZ")
```

**Fluxo:**
```
ptifrmtgtframe 
  ↓ Clicar lupa
default_content
  ↓
ptModFrame_1
  ↓ Buscar e selecionar
default_content
  ↓
ptifrmtgtframe
```

---

### 2. **Process Name Modal** (ptModFrame_2) ✅

```python
Modal Type: Process Name
Iframe: ptModFrame_2
Lupa ID: PMN_FILTER_WRK_PRCSNAME$prompt
Campo ID: PMN_PRCSNAME_VW_PRCSNAME
```

**Uso:**
```python
search_process_name_modal("AJ_LDEXP")
```

**Fluxo:**
```
ptifrmtgtframe 
  ↓ Clicar lupa
default_content
  ↓
ptModFrame_2
  ↓ Buscar e selecionar
default_content
  ↓
ptifrmtgtframe
```

---

## 🔧 Função Genérica Implementada

```python
def search_in_modal(search_value: str, modal_type: str, modal_frame: str, 
                    prompt_id: str, search_field_id: str, result_contains: str):
    """
    Função genérica para buscar em qualquer modal do PeopleSoft
    
    Parâmetros:
    - search_value: Valor a buscar (ex: "MBENITEZ")
    - modal_type: Tipo do modal para logs (ex: "User ID")
    - modal_frame: Nome do iframe (ex: "ptModFrame_1")
    - prompt_id: ID da lupa (ex: "PMN_FILTER_WRK_WS_OPRID$prompt")
    - search_field_id: ID do campo de busca (ex: "PMN_OPRID_VW_OPRID")
    - result_contains: Texto para encontrar no resultado (ex: user_id)
    """
```

### Exemplos de Uso:

#### User ID:
```python
search_in_modal(
    search_value="MBENITEZ",
    modal_type="User ID",
    modal_frame="ptModFrame_1",
    prompt_id="PMN_FILTER_WRK_WS_OPRID$prompt",
    search_field_id="PMN_OPRID_VW_OPRID",
    result_contains="MBENITEZ"
)
```

#### Process Name:
```python
search_in_modal(
    search_value="AJ_LDEXP",
    modal_type="Process Name",
    modal_frame="ptModFrame_2",
    prompt_id="PMN_FILTER_WRK_PRCSNAME$prompt",
    search_field_id="PMN_PRCSNAME_VW_PRCSNAME",
    result_contains="AJ_LDEXP"
)
```

---

## 🎨 Diagrama Visual

```
┌─────────────────────────────────────────────────────┐
│ PÁGINA PRINCIPAL (default_content)                  │
│                                                     │
│  ┌────────────────────────────────────────────┐   │
│  │ ptifrmtgtframe (iframe principal)          │   │
│  │                                            │   │
│  │  User ID: [_______] 🔍─────────┐          │   │
│  │  Server: [▼]                   │          │   │
│  │  Type: [▼]                     │          │   │
│  │  Name: [_______] 🔍────────┐   │          │   │
│  │                            │   │          │   │
│  │  [Process List Table]      │   │          │   │
│  └────────────────────────────┼───┼──────────┘   │
│                               │   │              │
│  ┌────────────────────────────┼───┼──────────┐   │
│  │ ptModFrame_1               │   │          │   │
│  │ (User ID Modal) ←──────────┘   │          │   │
│  │                                │          │   │
│  │  Search: [MBENITEZ____]        │          │   │
│  │  [Look Up]                     │          │   │
│  │                                │          │   │
│  │  Results:                      │          │   │
│  │  ☑ MBENITEZ                    │          │   │
│  │    AJPEOPLE                    │          │   │
│  │    ...                         │          │   │
│  └────────────────────────────────┘          │   │
│                                               │   │
│  ┌────────────────────────────────────────┐  │   │
│  │ ptModFrame_2                           │  │   │
│  │ (Process Name Modal) ←─────────────────┘  │   │
│  │                                           │   │
│  │  Search: [AJ_LDEXP____]                  │   │
│  │  [Look Up]                               │   │
│  │                                           │   │
│  │  Results:                                │   │
│  │  No matching values found                │   │
│  └──────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 📝 Resumo do Fluxo

### Para Qualquer Modal:

```python
# 1. Estar no iframe principal
driver.switch_to.frame("ptifrmtgtframe")

# 2. Clicar na lupa
driver.find_element(By.ID, prompt_id).click()

# 3. Voltar ao contexto padrão
driver.switch_to.default_content()

# 4. Entrar no iframe do modal
driver.switch_to.frame(modal_frame)  # ptModFrame_1, ptModFrame_2, etc.

# 5. Preencher e buscar
field = driver.find_element(By.ID, search_field_id)
field.send_keys(search_value)
# Busca automática ou clicar Look Up

# 6. Selecionar resultado
result.click()

# 7. Voltar ao iframe principal
driver.switch_to.default_content()
driver.switch_to.frame("ptifrmtgtframe")

# 8. Continuar com outros filtros...
```

---

## ✅ Benefícios da Função Genérica

1. **Reutilizável** - Funciona para qualquer modal
2. **Manutenível** - Um único lugar para corrigir bugs
3. **Consistente** - Mesmo comportamento em todos os modais
4. **Logs claros** - Identificação por modal_type
5. **Screenshots automáticos** - Em caso de erro

---

## 🚀 Como Adicionar Novo Modal

Se encontrar um novo modal (ex: Server modal em ptModFrame_3):

```python
def search_server_modal(server_name: str):
    """Busca Server usando o modal de lookup (iframe: ptModFrame_3)"""
    return search_in_modal(
        search_value=server_name,
        modal_type="Server",
        modal_frame="ptModFrame_3",          # ← Descobrir qual frame
        prompt_id="SERVER_FIELD$prompt",     # ← ID da lupa
        search_field_id="SERVER_VW_NAME",    # ← ID do campo
        result_contains=server_name
    )
```

**Passos:**
1. Inspecionar HTML do modal
2. Identificar o iframe (ptModFrame_X)
3. Identificar IDs da lupa e campo
4. Criar função usando `search_in_modal()`

---

## 📊 Tabela de Referência Rápida

| Modal | Iframe | Lupa ID | Campo ID | Status |
|-------|--------|---------|----------|--------|
| **User ID** | ptModFrame_1 | PMN_FILTER_WRK_WS_OPRID$prompt | PMN_OPRID_VW_OPRID | ✅ Implementado |
| **Process Name** | ptModFrame_2 | PMN_FILTER_WRK_PRCSNAME$prompt | PMN_PRCSNAME_VW_PRCSNAME | ✅ Pronto (não usado) |
| Server? | ptModFrame_? | ? | ? | ❓ Não mapeado |
| Type? | ptModFrame_? | ? | ? | ❓ Não mapeado |
| Outros... | ptModFrame_? | ? | ? | ❓ Não mapeado |

---

## 🎯 Conclusão

**Todos os modais seguem o mesmo padrão:**
- Cada modal tem seu próprio iframe (ptModFrame_X)
- Todos usam a mesma estrutura de busca
- A função genérica funciona para qualquer um

**Basta descobrir:**
1. Qual ptModFrame_X usar
2. ID da lupa
3. ID do campo de busca

E pronto! 🚀
