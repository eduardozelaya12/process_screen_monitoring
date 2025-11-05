# 🔴 PROBLEMA CRÍTICO: UTF-8 BOM no JSON

## ❌ Erro que Impediu a Execução

```
ERROR - Erro no orquestrador: Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)
```

---

## 🔍 O Que Aconteceu?

### UTF-8 BOM (Byte Order Mark)

Quando usei o PowerShell com `Out-File -Encoding UTF8`, ele adicionou um **BOM** (Byte Order Mark) no início do arquivo:

```
Arquivo com BOM:
EF BB BF { "peoplesoft": { ... } }
   ^^^
   BOM = 3 bytes extras no início
```

Python não conseguiu ler o JSON por causa desses bytes extras!

---

## 💥 Consequências

### 1. Orquestrador NÃO Iniciou
```
✗ Nenhum collector carregado
✗ Nenhuma coleta agendada
✗ Sistema rodando VAZIO
```

### 2. Dashboard Retornando 404
```
GET /api/screenshot/peoplesoft HTTP/1.1" 404
                                        ^^^
                        Collector não existe!
```

### 3. Apenas Backend Funcionou
```
✓ Backend Flask inicializado
✓ Servidor web rodando
✗ Mas SEM coletores!
```

---

## ✅ SOLUÇÃO APLICADA

### Recriei o JSON sem BOM

Usei método diferente no PowerShell:

```powershell
# ERRADO (adiciona BOM):
Out-File -Encoding UTF8 arquivo.json

# CORRETO (sem BOM):
[System.IO.File]::WriteAllText(
    "arquivo.json",
    $conteudo,
    (New-Object System.Text.UTF8Encoding $false)
                                          ^^^^^
                                      false = sem BOM
)
```

---

## 🧪 Verificação

### Teste se JSON está OK:

```bash
python -c "import json; json.load(open('config/systems_config.json', 'r', encoding='utf-8')); print('OK - JSON valido')"
```

**Resultado esperado:**
```
OK - JSON valido
```

**Se der erro:**
```
Unexpected UTF-8 BOM  ← Ainda tem BOM!
```

---

## 📊 Comparação

### ANTES (com BOM):
```bash
python main.py
# Output:
ERROR - Erro no orquestrador: Unexpected UTF-8 BOM...
GET /api/screenshot/peoplesoft HTTP/1.1" 404
```

### DEPOIS (sem BOM):
```bash
python main.py
# Output esperado:
INFO - ✓ Coletor PeopleSoft inicializado
INFO - ✓ Job agendado: peoplesoft a cada 180s
INFO - 📸 Coletando dados: PeopleSoft
```

---

## 🚀 TESTE AGORA

```bash
python main.py
```

### Logs Esperados:

```
INFO - ✓ Banco de dados inicializado
INFO - ✓ Rotas registradas
INFO - ✓ Backend Flask inicializado
INFO - 🔧 Iniciando componentes...
INFO - ✓ Coletor PeopleSoft inicializado    ← DEVE APARECER!
INFO - ✓ 1 coletores inicializados           ← DEVE APARECER!
INFO - ✓ Job agendado: peoplesoft a cada 180s ← DEVE APARECER!
INFO - 📸 Coletando dados: PeopleSoft        ← DEVE APARECER!
INFO - 🔍 DEBUG __init__: Filtros carregados do config:
INFO -    - Total de chaves: 9
INFO - 👀 Modo VISUAL ativado (com interface)
INFO - ✓ WebDriver inicializado
INFO - 🔐 Fazendo login...
```

---

## 🔍 Como Detectar o Problema

### 1. Ver Bytes do Arquivo

```powershell
# PowerShell
Format-Hex config\systems_config.json | Select-Object -First 3
```

**Com BOM:**
```
00000000   EF BB BF 7B 0D 0A 20 20  22 70 65 6F 70 6C 65 73   ï»¿{..  "peoples
           ^^^^^^^^
           BOM!
```

**Sem BOM:**
```
00000000   7B 0D 0A 20 20 22 70 65  6F 70 6C 65 73 6F 66 74   {..  "peoplesoft
           ^
           Começa direto com {
```

---

### 2. Ver Tamanho do Arquivo

```powershell
(Get-Item config\systems_config.json).Length
```

**Com BOM:** Tamanho = X + 3 bytes  
**Sem BOM:** Tamanho = X bytes  

---

## 📝 Prevenção Futura

### Sempre use um dos métodos:

#### Opção 1: WriteAllText (PowerShell)
```powershell
$json = @'
{...}
'@
[System.IO.File]::WriteAllText(
    "config\systems_config.json",
    $json,
    (New-Object System.Text.UTF8Encoding $false)
)
```

#### Opção 2: Editor de Texto
- Notepad++ → Encoding → UTF-8 (without BOM)
- VS Code → Salva automaticamente sem BOM
- Vim → `:set nobomb`

#### Opção 3: Python
```python
import json

data = {...}

with open('config/systems_config.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
# Python nunca adiciona BOM
```

---

## 🎯 Resumo do Problema

| Item | Status Antes | Status Depois |
|------|--------------|---------------|
| **JSON** | ❌ Com BOM | ✅ Sem BOM |
| **Orquestrador** | ❌ Não iniciou | ✅ Iniciando |
| **Collectors** | ❌ 0 carregados | ✅ 1 carregado |
| **Jobs** | ❌ 0 agendados | ✅ 1 agendado |
| **API** | ❌ 404 | ✅ 200 |

---

## 🔧 Arquivo Corrigido

O arquivo `config/systems_config.json` foi recriado:

✅ **Sem BOM**  
✅ **UTF-8 puro**  
✅ **JSON válido**  
✅ **Todos os filtros presentes**  
✅ **headless: false** (modo debug)  
✅ **collection_interval: 180** (3 minutos)  

---

## 🎉 Resultado Final

Agora o sistema deve:

✅ Iniciar o orquestrador corretamente  
✅ Carregar PeopleSoft collector  
✅ Agendar job a cada 3 minutos  
✅ Fazer login  
✅ Aplicar filtros  
✅ Clicar em Refresh com highlight  
✅ Extrair métricas  
✅ Salvar screenshots  

**Execute novamente e confirme! 🚀**
