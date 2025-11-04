# 🧪 GUIA DO TESTE MELHORADO

## 🎯 O Que Foi Corrigido

Analisei os logs e o HTML fornecido e identifiquei o problema:

### ❌ Problema Anterior
```
>> Não foi possível trocar para iframe; tentando no contexto atual…
[Aviso] Não foi possível ajustar PMN_FILTER_WRK_SERVERNAME: ...
[Aviso] Não foi possível ajustar PMN_FILTER_WRK_RUNSTATUS: ...
[Aviso] Não foi possível clicar em Refresh: ...
```

**Causa Raiz:** Os elementos **ESTÃO dentro do iframe `ptifrmtgtframe`**, mas o código não estava fazendo o switch corretamente.

---

## ✅ Melhorias Implementadas

### 1. **Detecção Inteligente de Iframes**

```python
# Lista TODOS os iframes da página
iframes = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
print(f">> {len(iframes)} frames encontrados na página")
for idx, frame in enumerate(iframes):
    frame_id = frame.get_attribute('id') or '(sem id)'
    frame_name = frame.get_attribute('name') or '(sem name)'
    print(f"   Frame {idx}: id='{frame_id}', name='{frame_name}'")
```

**Benefício:** Você verá TODOS os iframes disponíveis e poderá confirmar se `ptifrmtgtframe` existe.

### 2. **Múltiplas Tentativas de Switch**

```python
# Tentativa 1: Por NAME (padrão PeopleSoft)
WebDriverWait(driver, 5).until(
    EC.frame_to_be_available_and_switch_to_it((By.NAME, "ptifrmtgtframe"))
)

# Tentativa 2: Por ID (caso NAME não funcione)
WebDriverWait(driver, 5).until(
    EC.frame_to_be_available_and_switch_to_it((By.ID, "ptifrmtgtframe"))
)

# Tentativa 3: Por índice (usa primeiro iframe encontrado)
driver.switch_to.frame(iframes[0])
```

**Benefício:** Se uma forma falhar, tenta outras automaticamente.

### 3. **Logs Detalhados de Filtros**

```python
def set_select_by_id(select_id: str, value_or_text: str):
    print(f"   Procurando elemento: {select_id}")
    elem = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, select_id))
    )
    print(f"   ✓ Elemento {select_id} encontrado")
    
    # Mostra opções disponíveis
    options = [opt.get_attribute('value') for opt in sel.options]
    print(f"   Opções disponíveis: {options[:5]}...")
    
    # Tenta por value
    sel.select_by_value(value_or_text)
    print(f"   ✓ {select_id} ajustado para '{value_or_text}' (por value)")
```

**Benefício:** Você verá EXATAMENTE onde está falhando e por quê.

### 4. **Múltiplas Tentativas no Botão Refresh**

```python
# Tentativa 1: Por ID padrão
refresh_btn = WebDriverWait(driver, 5).until(
    EC.element_to_be_clickable((By.ID, "REFRESH_BTN"))
)

# Tentativa 2: Por texto do botão
refresh_btn = driver.find_element(By.XPATH, "//input[@value='Refresh']")

# Tentativa 3: Por parte do ID
refresh_btn = driver.find_element(By.XPATH, "//*[contains(@id, 'REFRESH')]")
```

**Benefício:** Tenta todas as formas possíveis de encontrar o botão.

---

## 🚀 Como Executar o Teste

### Passo 1: Execute o teste
```bash
python test_peoplesoft.py
```

### Passo 2: Preencha os filtros quando solicitado

```
=== Filtros opcionais (pressione Enter para pular) ===
Server (ex.: PSUNX, AJNODE4B…): PSUNX
Run Status (vazio/1 Cancel, 3 Error, 9 Success, 10 No Success, 7 Processing, 17 Warning… informe o valor numérico): 9
Type (ex.: Application Engine, PSJob, SQR Report…): Application Engine
Distribution Status (vazio/5 Posted/3 Generated/4 Not Posted/2 Processing… informe o valor numérico): 5
Time Filter valor (número, ex.: 1): [Enter para pular]
Time Filter unidade (0 All / 1 Days / 2 Hours / 3 Minutes / 4 Years): [Enter para pular]
```

---

## 📊 Saída Esperada (Sucesso)

### ✅ Com as Melhorias - Deve Ver:

```
>> Navegando para monitor de processos...
>> 3 frames encontrados na página
   Frame 0: id='TargetContent', name='TargetContent'
   Frame 1: id='ptifrmtgtframe', name='ptifrmtgtframe'  ← ESTE É O IMPORTANTE!
   Frame 2: id='(sem id)', name='(sem name)'
>> ✓ Switch para iframe ptifrmtgtframe OK (por NAME)

=== Filtros opcionais (pressione Enter para pular) ===
Server (ex.: PSUNX, AJNODE4B…): PSUNX

   Procurando elemento: PMN_FILTER_WRK_SERVERNAME
   ✓ Elemento PMN_FILTER_WRK_SERVERNAME encontrado
   Opções disponíveis: ['', 'AJNODE4B', 'AJNODE4C', 'PSCDB', 'PSNT']...
   ✓ PMN_FILTER_WRK_SERVERNAME ajustado para 'PSUNX' (por value)

Run Status (...): 9

   Procurando elemento: PMN_FILTER_WRK_RUNSTATUS
   ✓ Elemento PMN_FILTER_WRK_RUNSTATUS encontrado
   Opções disponíveis: ['', '18', '1', '8', '3']...
   ✓ PMN_FILTER_WRK_RUNSTATUS ajustado para '9' (por value)

Type (ex.: Application Engine, PSJob, SQR Report…): Application Engine

   Procurando elemento: PMN_FILTER_WRK_PRCSTYPE
   ✓ Elemento PMN_FILTER_WRK_PRCSTYPE encontrado
   Opções disponíveis: ['', 'Application Engine', 'XML Publisher', 'Cube Builder', 'COBOL SQL']...
   ✓ PMN_FILTER_WRK_PRCSTYPE ajustado para 'Application Engine' (por value)

>> Tentando clicar no botão Refresh...
   ✓ Refresh clicado (por ID)
>> Aguardando atualização da grid...

>> Título após navegação: Process Monitor
>> URL após navegação: http://pswebt1.ajover.com:8080/psp/erptest/...
[OK] Tela do monitor potencialmente acessível.
```

---

## 🔍 Diagnóstico de Problemas

### Caso 1: "Nenhum iframe encontrado"

```
>> 0 frames encontrados na página
```

**Causa:** Página não carregou completamente ou estrutura diferente.

**Solução:**
1. Aumentar `time.sleep(4)` para `time.sleep(6)` após `driver.get()`
2. Verificar se URL está correta
3. Verificar se login funcionou

### Caso 2: "Iframe existe mas switch falha"

```
>> 2 frames encontrados na página
   Frame 0: id='ptifrmtgtframe', name='ptifrmtgtframe'
>> Tentativa por NAME falhou: TimeoutException
>> Tentativa por ID falhou: TimeoutException
>> Tentativa por índice falhou: ...
```

**Causa:** Iframe não está pronto ou bloqueado.

**Solução:**
1. Aumentar timeout de 5s para 10s
2. Verificar se há popup/overlay bloqueando
3. Tentar aguardar mais após navegação

### Caso 3: "Elemento não encontrado após switch"

```
>> ✓ Switch para iframe ptifrmtgtframe OK (por NAME)
   ❌ ERRO ao ajustar PMN_FILTER_WRK_SERVERNAME: NoSuchElementException
```

**Causa:** Elemento não carregou ainda ou ID está errado.

**Solução:**
1. Aumentar `time.sleep(2)` após switch
2. Verificar ID correto no HTML (usar `dump_monitor.html`)
3. Verificar se há múltiplos iframes aninhados

---

## 📝 Mapeamento de Valores dos Filtros

Com base no HTML fornecido:

### Server (PMN_FILTER_WRK_SERVERNAME)
```
Valores válidos:
- "AJNODE4B"
- "AJNODE4C"
- "PSCDB"
- "PSNT"
- "PSOS390"
- "PSUNX"  ← Você usou este
```

### Run Status (PMN_FILTER_WRK_RUNSTATUS)
```
Valores válidos (são NÚMEROS):
- "1"  → Cancel
- "3"  → Error
- "4"  → Hold
- "5"  → Queued
- "6"  → Initiated
- "7"  → Processing
- "8"  → Cancelled
- "9"  → Success  ← Você usou este
- "10" → No Success
- "16" → Pending
- "17" → Warning
- "18" → Blocked
- "19" → Restart
```

### Type (PMN_FILTER_WRK_PRCSTYPE)
```
Valores válidos:
- "Application Engine"  ← Você usou este
- "XML Publisher"
- "Cube Builder"
- "COBOL SQL"
- "Crystal"
- "PSJob"
- "SQR Process"
- "SQR Report"
- "Winword"
- "nVision"
... etc
```

### Distribution Status (PMN_FILTER_WRK_DISTSTATUS)
```
Valores válidos (são NÚMEROS):
- "0" → None
- "1" → N/A
- "2" → Processing
- "3" → Generated
- "4" → Not Posted
- "5" → Posted  ← Você pode usar este
- "6" → Delete
- "7" → Posting
- "9" → Pending
```

---

## 🎯 Próximos Passos

### 1. Execute o teste melhorado
```bash
python test_peoplesoft.py
```

### 2. Analise os novos logs

Se ainda falhar, você verá EXATAMENTE onde e por quê:
- Quantos iframes existem
- Qual iframe foi usado
- Se cada elemento foi encontrado
- Quais opções estão disponíveis
- Onde cada tentativa falhou

### 3. Compartilhe os novos logs

Se ainda houver problema, os novos logs terão MUITO mais informação para diagnosticar.

---

## ✅ Aplicar no Código de Produção

Depois que o teste funcionar, as mesmas melhorias podem ser aplicadas no `peoplesoft_collector.py`:

```python
# collectors/peoplesoft_collector.py
def _capture_and_extract(self):
    # ... código existente ...
    
    # Usar a mesma lógica de múltiplas tentativas
    iframe_switched = False
    try:
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe") + self.driver.find_elements(By.TAG_NAME, "frame")
        logger.info(f"Frames encontrados: {len(iframes)}")
        
        # Tentativa 1: Por NAME
        try:
            WebDriverWait(self.driver, 5).until(
                EC.frame_to_be_available_and_switch_to_it((By.NAME, "ptifrmtgtframe"))
            )
            logger.info("✓ Switch para iframe ptifrmtgtframe")
            iframe_switched = True
        except Exception:
            # Tentativa 2: Por índice
            if iframes:
                self.driver.switch_to.frame(iframes[0])
                logger.info("✓ Switch para primeiro iframe")
                iframe_switched = True
    except Exception as e:
        logger.error(f"Erro ao processar iframes: {e}")
```

---

## 📄 Arquivos Gerados pelo Teste

Após execução, verifique:

```
storage/logs/
├── navegacao_monitor.png       ← Screenshot da tela final
├── dump_monitor.html           ← HTML completo da página
├── cookies_aplicados.png       ← (se rodar test_cookies_acessam_monitor)
└── cookies_test_monitor.html   ← (se rodar test_cookies_acessam_monitor)
```

**Use estes arquivos para:**
- Verificar visualmente se página carregou
- Inspecionar HTML para encontrar IDs corretos
- Confirmar se filtros foram aplicados
- Ver estrutura de iframes

---

## 🎉 Resultado Esperado

Se tudo funcionar, ao final você verá a tabela de processos filtrada conforme suas escolhas:

```
Process List
Select Instance  Seq.  Process Type       Process Name  User      Run Date/Time
□      7997158        Application Engine  AJ_LDEXP      MBENITEZ  03/11/2025...
□      7997157        Application Engine  AJ_LDEXP      MBENITEZ  03/11/2025...
```

E o log confirmará:
```
[OK] Tela do monitor potencialmente acessível.
```

---

**Execute o teste agora e compartilhe os novos logs! 🚀**
