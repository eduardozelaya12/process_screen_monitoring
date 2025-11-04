# 🎛️ GUIA COMPLETO DE FILTROS - PeopleSoft Process Monitor

## 🎯 Todos os Filtros Implementados

Agora o teste suporta **TODOS os filtros** disponíveis no Process Monitor do PeopleSoft!

---

## 📋 Lista de Filtros

### 1. **User ID** 🔍 COM MODAL
```
Descrição: Filtra por usuário que executou o processo
Tipo: Busca via modal (lookup)
Exemplo: MBENITEZ, AJPEOPLE, BMILLAN

Como funciona:
1. Abre modal de busca
2. Preenche campo de busca
3. Clica "Look Up"
4. Seleciona resultado da lista
```

**IDs no HTML:**
- Lupa: `PMN_FILTER_WRK_WS_OPRID$prompt`
- Campo busca: `PMN_OPRID_VW_OPRID`
- Botão buscar: `#ICSearch`
- Resultado: Link na tabela `PTSRCHRESULTS`

---

### 2. **Server** 🖥️
```
Descrição: Servidor onde o processo foi executado
Tipo: Dropdown (select)
ID: PMN_FILTER_WRK_SERVERNAME

Valores disponíveis:
- AJNODE4B
- AJNODE4C
- PSCDB
- PSNT
- PSOS390
- PSUNX

Exemplo de uso: PSUNX
```

---

### 3. **Run Status** ✅❌
```
Descrição: Status de execução do processo
Tipo: Dropdown (select)
ID: PMN_FILTER_WRK_RUNSTATUS

Valores disponíveis (são NÚMEROS):
- 1  → Cancel
- 3  → Error
- 4  → Hold
- 5  → Queued
- 6  → Initiated
- 7  → Processing
- 8  → Cancelled
- 9  → Success       ← MAIS COMUM
- 10 → No Success
- 16 → Pending
- 17 → Warning
- 18 → Blocked
- 19 → Restart

Exemplo de uso: 9 (para ver processos bem-sucedidos)
```

---

### 4. **Type** 📊
```
Descrição: Tipo do processo
Tipo: Dropdown (select)
ID: PMN_FILTER_WRK_PRCSTYPE

Valores disponíveis:
- Application Engine    ← MAIS COMUM
- XML Publisher
- Cube Builder
- COBOL SQL
- Crystal
- Crystal Check
- Data Mover
- Database Agent
- Demand Planning Upload
- Essbase
- Essbase Cube Builder
- HyperCube Builder
- Message Agent API
- Optimization Engine
- PSJob
- SQR PO-Special Process
- SQR Process
- SQR Report
- SQR Report For WF Delivery
- Winword
- nVision
- nVision Report
- nVision-ReportBook

Exemplo de uso: Application Engine
```

---

### 5. **Distribution Status** 📤
```
Descrição: Status de distribuição do output
Tipo: Dropdown (select)
ID: PMN_FILTER_WRK_DISTSTATUS

Valores disponíveis (são NÚMEROS):
- 0 → None
- 1 → N/A
- 2 → Processing
- 3 → Generated
- 4 → Not Posted
- 5 → Posted         ← MAIS COMUM
- 6 → Delete
- 7 → Posting
- 9 → Pending

Exemplo de uso: 5 (para ver processos com output postado)
```

---

### 6. **Instance From/To** 🔢
```
Descrição: Faixa de números de instância do processo
Tipo: Campos de texto numéricos
IDs: 
  - PMN_DERIVED_PRCSINSTANCE (From)
  - PMN_DERIVED_TO_PRCSINSTANCE (To)

Valores: Números inteiros (ex.: 7997100 até 7997200)

Exemplo de uso:
  Instance From: 7997100
  Instance To: 7997200

Útil para buscar um range específico de processos.
```

---

### 7. **Time Filter** ⏰ (3 campos)

#### 7a. Time Filter Type
```
Descrição: Tipo de filtro de tempo
Tipo: Dropdown (select)
ID: PMN_FILTER_WRK_PT_FILTERTYPE

Valores disponíveis:
- 0 → Last          ← PADRÃO (últimos X dias/horas)
- 1 → Date Range    (intervalo específico de datas)

Exemplo de uso: 0 (Last)
```

#### 7b. Time Filter Value
```
Descrição: Valor numérico do filtro de tempo
Tipo: Campo de texto numérico
ID: PMN_FILTER_WRK_PT_FILTERVALUE

Valores: Números inteiros (ex.: 1, 7, 30, 70)

Exemplo de uso: 70 (últimos 70 dias)
```

#### 7c. Time Filter Unit
```
Descrição: Unidade de tempo
Tipo: Dropdown (select)
ID: PMN_FILTER_WRK_PT_FILTERUNIT

Valores disponíveis:
- 0 → All
- 1 → Days          ← MAIS COMUM
- 2 → Hours
- 3 → Minutes
- 4 → Years

Exemplo de uso: 1 (Days)

Combinado: "Last 70 Days"
  Type = 0 (Last)
  Value = 70
  Unit = 1 (Days)
```

---

## 🚀 Como Usar o Teste

### Executar o teste:
```bash
python test_peoplesoft.py
```

### Exemplo de entrada completa:
```
============================================================
FILTROS DISPONÍVEIS (pressione Enter para pular)
============================================================

1. User ID (ex.: MBENITEZ, AJPEOPLE...): MBENITEZ

2. Server (ex.: PSUNX, AJNODE4B, AJNODE4C...): PSUNX

3. Run Status:
   1=Cancel, 3=Error, 7=Processing, 8=Cancelled
   9=Success, 10=No Success, 17=Warning, 18=Blocked
   Valor: 9

4. Type:
   Application Engine, PSJob, SQR Report, Crystal...
   Valor: Application Engine

5. Distribution Status:
   2=Processing, 3=Generated, 4=Not Posted, 5=Posted, 9=Pending
   Valor: 5

6. Instance From (número, ex.: 7997100): 7997100
   Instance To (número, ex.: 7997200): 7997200

7. Time Filter:
   Type: 0=Last (padrão), 1=Date Range
   Type: 0
   Value (número, ex.: 70): 70
   Unit: 0=All, 1=Days, 2=Hours, 3=Minutes, 4=Years
   Unit: 1

============================================================
```

---

## 📊 Saída Esperada

### ✅ Aplicação de Filtros (Sucesso):

```
============================================================
APLICANDO FILTROS...
============================================================

>> Buscando User ID 'MBENITEZ' via modal...
   1. Clicando na lupa de User ID...
   2. Preenchendo campo de busca...
   3. Clicando em Look Up...
   4. Procurando resultado...
   ✓ User ID 'MBENITEZ' selecionado!

>> Aplicando filtro Server...
   Procurando elemento: PMN_FILTER_WRK_SERVERNAME
   ✓ Elemento PMN_FILTER_WRK_SERVERNAME encontrado
   Opções disponíveis: ['', 'AJNODE4B', 'AJNODE4C', 'PSCDB', 'PSNT']...
   ✓ PMN_FILTER_WRK_SERVERNAME ajustado para 'PSUNX' (por value)

>> Aplicando filtro Run Status...
   Procurando elemento: PMN_FILTER_WRK_RUNSTATUS
   ✓ Elemento PMN_FILTER_WRK_RUNSTATUS encontrado
   ✓ PMN_FILTER_WRK_RUNSTATUS ajustado para '9' (por value)

>> Aplicando filtro Type...
   Procurando elemento: PMN_FILTER_WRK_PRCSTYPE
   ✓ Elemento PMN_FILTER_WRK_PRCSTYPE encontrado
   ✓ PMN_FILTER_WRK_PRCSTYPE ajustado para 'Application Engine' (por value)

>> Aplicando filtro Distribution Status...
   Procurando elemento: PMN_FILTER_WRK_DISTSTATUS
   ✓ Elemento PMN_FILTER_WRK_DISTSTATUS encontrado
   ✓ PMN_FILTER_WRK_DISTSTATUS ajustado para '5' (por value)

>> Aplicando filtro Instance From...
   Procurando campo de texto: PMN_DERIVED_PRCSINSTANCE
   ✓ Instance From ajustado para '7997100'

>> Aplicando filtro Instance To...
   Procurando campo de texto: PMN_DERIVED_TO_PRCSINSTANCE
   ✓ Instance To ajustado para '7997200'

>> Aplicando Time Filter Type...
   Procurando elemento: PMN_FILTER_WRK_PT_FILTERTYPE
   ✓ Elemento PMN_FILTER_WRK_PT_FILTERTYPE encontrado
   ✓ PMN_FILTER_WRK_PT_FILTERTYPE ajustado para '0' (por value)

>> Aplicando Time Filter Value...
   Procurando campo de texto: PMN_FILTER_WRK_PT_FILTERVALUE
   ✓ Time Filter Value ajustado para '70'

>> Aplicando Time Filter Unit...
   Procurando elemento: PMN_FILTER_WRK_PT_FILTERUNIT
   ✓ Elemento PMN_FILTER_WRK_PT_FILTERUNIT encontrado
   ✓ PMN_FILTER_WRK_PT_FILTERUNIT ajustado para '1' (por value)

>> Tentando clicar no botão Refresh...
   ✓ Refresh clicado (por ID)
>> Aguardando atualização da grid...

>> Título após navegação: Process Monitor
>> URL após navegação: http://pswebt1.ajover.com:8080/psp/erptest/...
[OK] Tela do monitor potencialmente acessível.
```

---

## 💡 Dicas de Uso

### Cenário 1: Ver todos os processos de um usuário
```
User ID: MBENITEZ
(deixar resto em branco)
```

### Cenário 2: Ver processos com erro nos últimos 7 dias
```
Run Status: 3 (Error)
Time Filter Type: 0 (Last)
Time Filter Value: 7
Time Filter Unit: 1 (Days)
```

### Cenário 3: Ver Application Engines bem-sucedidos de hoje
```
Type: Application Engine
Run Status: 9 (Success)
Time Filter Type: 0 (Last)
Time Filter Value: 1
Time Filter Unit: 1 (Days)
```

### Cenário 4: Ver processos de um range específico
```
Instance From: 7997100
Instance To: 7997150
```

### Cenário 5: Análise completa (todos os filtros)
```
User ID: MBENITEZ
Server: PSUNX
Run Status: 9
Type: Application Engine
Distribution Status: 5
Instance From: 7997000
Instance To: 7998000
Time Filter Type: 0
Time Filter Value: 30
Time Filter Unit: 1
```

---

## 🔍 Filtros Não Implementados (por enquanto)

### Name (Process Name) ❌
```
Motivo: Você mencionou que não retorna resultados na página
Se necessário, pode ser implementado igual ao User ID:
- Lupa: PMN_FILTER_WRK_PRCSNAME$prompt
- Campo: PMN_PRCSNAME_VW_PRCSNAME
- Botão: #ICSearch
```

---

## 📝 Mapeamento Completo de IDs

| Filtro | Tipo | ID HTML |
|--------|------|---------|
| User ID (lupa) | Link | `PMN_FILTER_WRK_WS_OPRID$prompt` |
| User ID (busca) | Input | `PMN_OPRID_VW_OPRID` |
| User ID (Look Up) | Button | `#ICSearch` |
| Server | Select | `PMN_FILTER_WRK_SERVERNAME` |
| Run Status | Select | `PMN_FILTER_WRK_RUNSTATUS` |
| Type | Select | `PMN_FILTER_WRK_PRCSTYPE` |
| Distribution Status | Select | `PMN_FILTER_WRK_DISTSTATUS` |
| Instance From | Input | `PMN_DERIVED_PRCSINSTANCE` |
| Instance To | Input | `PMN_DERIVED_TO_PRCSINSTANCE` |
| Time Filter Type | Select | `PMN_FILTER_WRK_PT_FILTERTYPE` |
| Time Filter Value | Input | `PMN_FILTER_WRK_PT_FILTERVALUE` |
| Time Filter Unit | Select | `PMN_FILTER_WRK_PT_FILTERUNIT` |
| Refresh Button | Button | `REFRESH_BTN` |

---

## 🎯 Próximos Passos

### 1. Testar os novos filtros
```bash
python test_peoplesoft.py
```

### 2. Validar resultados

Após aplicar filtros, verificar:
- Screenshot: `storage/logs/navegacao_monitor.png`
- HTML: `storage/logs/dump_monitor.html`
- Tabela de processos foi filtrada corretamente

### 3. Aplicar no código de produção

Quando os testes funcionarem, implementar as mesmas funcionalidades no `peoplesoft_collector.py`.

---

## 🚨 Troubleshooting

### Problema: User ID não encontrado
```
>> ⚠️ User ID 'XXX' não encontrado nos resultados
```
**Solução:** Verifique se o User ID existe no sistema. Tente buscar manualmente na interface.

### Problema: Modal não fecha
```
Modal fica aberto após busca
```
**Solução:** O código já tenta clicar em Cancel se não encontrar resultado.

### Problema: Filtros não aplicam
```
❌ ERRO ao ajustar PMN_FILTER_WRK_SERVERNAME...
```
**Solução:** Certifique-se que fez switch para o iframe `ptifrmtgtframe`.

---

## ✅ Resumo

Agora o teste suporta **9 filtros diferentes**:

1. ✅ **User ID** (com modal)
2. ✅ **Server**
3. ✅ **Run Status**
4. ✅ **Type**
5. ✅ **Distribution Status**
6. ✅ **Instance From**
7. ✅ **Instance To**
8. ✅ **Time Filter Type**
9. ✅ **Time Filter Value**
10. ✅ **Time Filter Unit**

Todos com:
- ✅ Logs detalhados
- ✅ Tratamento de erros
- ✅ Múltiplas tentativas
- ✅ Mensagens claras

**Execute o teste e veja a mágica acontecer! 🚀**
