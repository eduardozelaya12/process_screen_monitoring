# 🔧 CORREÇÃO: User ID Modal - Timeout Resolvido

## ❌ Problema Identificado

```
❌ ERRO ao buscar User ID: TimeoutException
```

**Causa:** Timeouts muito curtos e seletores únicos que podem falhar.

---

## ✅ Correções Implementadas

### 1. **Timeouts Aumentados**

#### Antes:
```python
lupa = WebDriverWait(driver, 5).until(...)  # 5 segundos
time.sleep(2)  # Apenas 2 segundos após abrir modal
```

#### Depois:
```python
lupa = WebDriverWait(driver, 10).until(...)  # 10 segundos
time.sleep(4)  # 4 segundos após abrir modal - modal precisa carregar completamente
```

**Benefício:** Mais tempo para elementos carregarem, especialmente em rede lenta.

---

### 2. **Múltiplos Seletores (Fallback)**

#### Para o Campo de Busca:
```python
selectors = [
    (By.ID, "PMN_OPRID_VW_OPRID"),                              # Seletor principal
    (By.XPATH, "//input[contains(@id, 'OPRID')]"),             # Qualquer input com OPRID
    (By.XPATH, "//input[@type='text' and contains(@class, 'PSEDITBOX')]")  # Por classe
]

for by, selector in selectors:
    try:
        search_field = WebDriverWait(driver, 5).until(...)
        break  # Achou! Para de tentar
    except:
        continue  # Falhou, tenta próximo
```

**Benefício:** Se um seletor falhar, tenta outros automaticamente.

---

#### Para o Botão Look Up:
```python
button_selectors = [
    (By.ID, "#ICSearch"),                                      # ID principal
    (By.XPATH, "//input[@id='#ICSearch']"),                    # XPath do ID
    (By.XPATH, "//input[@value='Look Up']"),                   # Por texto do botão
    (By.XPATH, "//input[contains(@class, 'PSPUSHBUTTONTBLOOKUP')]")  # Por classe
]
```

**Benefício:** Garante que o botão será encontrado mesmo se estrutura mudar.

---

#### Para o Resultado:
```python
result_selectors = [
    (By.XPATH, f"//a[contains(@class, 'PSSRCHRESULTS') and contains(text(), '{user_id.upper()}')]"),
    (By.XPATH, f"//a[contains(text(), '{user_id.upper()}')]"),
    (By.XPATH, f"//td[contains(text(), '{user_id.upper()}')]/a"),
    (By.LINK_TEXT, user_id.upper()),
    (By.ID, "SEARCH_RESULT1")  # Primeiro resultado da lista
]
```

**Benefício:** Múltiplas formas de encontrar o resultado.

---

### 3. **Try/Except Individuais**

#### Antes:
```python
try:
    # Todo o código aqui
    # Se qualquer parte falhar, tudo falha
except Exception as e:
    print(f"ERRO: {e}")
```

#### Depois:
```python
# Etapa 1: Clicar na lupa
try:
    lupa = ...
    lupa.click()
except Exception as e:
    print(f"Erro na lupa: {e}")
    return False  # Falhou aqui, para

# Etapa 2: Preencher campo
try:
    search_field = ...
    search_field.send_keys(user_id)
except Exception as e:
    print(f"Erro no campo: {e}")
    return False  # Falhou aqui, para

# ... etc
```

**Benefício:** Logs mostram EXATAMENTE qual etapa falhou.

---

### 4. **Screenshot de Erro**

```python
except Exception as e:
    print(f"ERRO GERAL: {e}")
    try:
        driver.save_screenshot("storage/logs/erro_user_id_modal.png")
        print("📸 Screenshot salvo para debug")
    except:
        pass
```

**Benefício:** Se falhar, você terá uma imagem do estado da página para debugar.

---

### 5. **Esperas Estratégicas**

```python
driver.execute_script("arguments[0].click();", lupa)
time.sleep(4)  # ← NOVO: Aguardar modal abrir completamente

search_field.send_keys(user_id)
time.sleep(1)  # ← NOVO: Aguardar texto aparecer

driver.execute_script("arguments[0].click();", lookup_btn)
time.sleep(3)  # ← NOVO: Aguardar resultados carregarem

driver.execute_script("arguments[0].click();", result_link)
time.sleep(2)  # ← NOVO: Aguardar modal fechar
```

**Benefício:** Garante que cada ação complete antes de próxima.

---

## 📊 Saída Esperada AGORA

### ✅ Sucesso:
```
>> Buscando User ID 'MBENITEZ' via modal...
   1. Clicando na lupa de User ID...
   ✓ Lupa clicada, aguardando modal abrir...
   2. Preenchendo campo de busca...
   ✓ Campo encontrado com: PMN_OPRID_VW_OPRID
   ✓ Digitado 'MBENITEZ' no campo
   3. Clicando em Look Up...
   ✓ Botão encontrado com: //input[@value='Look Up']
   ✓ Botão Look Up clicado, aguardando resultados...
   4. Procurando resultado...
   ✓ Resultado encontrado com: //a[contains(text(), 'MBENITEZ')]
   ✓ User ID 'MBENITEZ' selecionado!
```

### ⚠️ Se Falhar (agora com mais detalhes):
```
>> Buscando User ID 'MBENITEZ' via modal...
   1. Clicando na lupa de User ID...
   ✓ Lupa clicada, aguardando modal abrir...
   2. Preenchendo campo de busca...
   ❌ Erro ao preencher campo: NoSuchElementException
   
   OU
   
   3. Clicando em Look Up...
   ❌ Erro ao clicar em Look Up: ElementNotInteractableException
   
   📸 Screenshot do erro salvo em: storage/logs/erro_user_id_modal.png
```

---

## 🧪 Como Testar

```bash
python test_peoplesoft.py
```

**Preencha quando pedir:**
```
1. User ID (ex.: MBENITEZ, AJPEOPLE...): MBENITEZ
```

**Aguarde os novos logs detalhados mostrarem cada etapa.**

---

## 🔍 Debug de Problemas

### Se ainda der timeout na etapa 2 (campo de busca):

**Possível causa:** Modal pode ter iframe interno.

**Solução:** Adicionar switch para iframe do modal:
```python
# Após abrir modal, antes de preencher campo:
try:
    WebDriverWait(driver, 3).until(
        EC.frame_to_be_available_and_switch_to_it((By.ID, "ptModFrame_0"))
    )
except:
    pass  # Sem iframe, continua
```

### Se campo não for encontrado:

**Verifique screenshot:** `storage/logs/erro_user_id_modal.png`

**Inspecione HTML do modal:**
```python
# Adicione após abrir modal:
with open("storage/logs/modal_html.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)
```

---

## 📝 Linha do Tempo da Função

```
Tempo Total: ~15 segundos (pior caso)

0s   → Clicar na lupa
0-10s → Aguardar lupa ficar clicável (timeout 10s)
10s   → Lupa clicada
10-14s → Aguardar modal abrir (sleep 4s)
14s   → Procurar campo de busca
14-19s → Aguardar campo aparecer (timeout 5s)
19s   → Campo encontrado
19-20s → Digitar texto (sleep 0.5s + 0.5s)
20s   → Procurar botão Look Up
20-25s → Aguardar botão (timeout 5s)
25s   → Botão clicado
25-28s → Aguardar resultados (sleep 3s)
28s   → Procurar resultado
28-33s → Aguardar resultado (timeout 5s)
33s   → Resultado clicado
33-35s → Aguardar modal fechar (sleep 2s)
35s   → ✓ CONCLUÍDO!
```

---

## ⚡ Otimizações Futuras (Opcional)

Se funcionar mas estiver muito lento, pode reduzir:

```python
# Reduzir para ambientes rápidos:
time.sleep(2)  # Em vez de 4 após abrir modal
time.sleep(1.5)  # Em vez de 3 após Look Up
```

Mas **PRIMEIRO confirme que funciona** com timeouts maiores!

---

## ✅ Resumo das Melhorias

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Timeout lupa | 5s | **10s** |
| Sleep após modal | 2s | **4s** |
| Sleep após Look Up | 2s | **3s** |
| Seletores | 1 por elemento | **3-5 por elemento** |
| Try/Except | 1 geral | **1 por etapa** |
| Logs | Básicos | **Detalhados** |
| Screenshot erro | ❌ Não | **✅ Sim** |
| Espera total | ~10s | **~15s** |

---

**Execute o teste novamente e compartilhe os novos logs! 🚀**

Agora deve funcionar sem timeout, e se ainda falhar, os logs mostrarão EXATAMENTE onde.
