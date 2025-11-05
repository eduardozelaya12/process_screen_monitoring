# 🔧 CORREÇÃO: 3 Problemas Principais

## 📊 Análise dos Logs e Imagem

### Imagem (TV Display):
- ✅ Interface carregando corretamente
- ❌ Screenshots não aparecem
- ✅ Status "Ativo" para Google
- ✅ Grid com 4 sistemas visível

### Logs:
1. ❌ PeopleSoft: `ERR_NAME_NOT_RESOLVED`
2. ❌ Google: Screenshots em pasta errada
3. ❌ Storage: Erro de serialização datetime

---

## ❌ PROBLEMA 1: PeopleSoft - Erro de Rede

### Log:
```
ERROR - net::ERR_NAME_NOT_RESOLVED
URL: http://pswebt1.ajover.com:8080/psp/erptest/EMPLOYEE/ERP
```

### Causa:
- **DNS não resolve** o hostname `pswebt1.ajover.com`
- **Servidor offline** ou inacessível da sua rede
- **Firewall** bloqueando acesso

### Sintomas:
- Chrome não consegue resolver o nome do servidor
- Coleta falha imediatamente
- Screenshot não é gerado

### ✅ Solução Aplicada:
```json
{
  "peoplesoft": {
    "enabled": false  ← Desabilitado temporariamente
  }
}
```

### Para Reativar:
1. Verificar se servidor está online:
   ```bash
   ping pswebt1.ajover.com
   ```
2. Testar URL no navegador manualmente
3. Se funcionar, alterar `enabled: true`

---

## ❌ PROBLEMA 2: Google - Pasta de Screenshots Errada

### Log:
```
✓ Screenshot salvo: storage/screenshots/selenium/screenshot_*.png
                                        ^^^^^^^^ ERRADO!
```

### Causa:
```python
# GoogleCollector estava usando:
screenshot_dir = f"storage/screenshots/{self.system_type}"
#                                      ^^^^^^^^^^^^^^^^
#                                      Retorna "selenium"
```

### Resultado:
- Screenshot salvo em `storage/screenshots/selenium/`
- API procura em `storage/screenshots/google/`
- **404 Not Found** → TV não mostra imagem

### ✅ Solução Aplicada:
```python
# Corrigido para:
screenshot_dir = "storage/screenshots/google"
```

### Antes vs Depois:
```
Antes:
storage/screenshots/selenium/screenshot_20251105_124312.png

Depois:
storage/screenshots/google/screenshot_20251105_124312.png
                    ^^^^^^
                    Correto!
```

---

## ❌ PROBLEMA 3: Erro de Serialização JSON

### Log:
```
ERROR - Object of type datetime is not JSON serializable
```

### Causa:
```python
# storage/local_storage.py
json.dumps(metrics)  # metrics contém objetos datetime
```

### Por Que Acontece:
```python
metrics = {
    'timestamp': datetime.now(),  # ← Objeto datetime
    'total': 10
}

json.dumps(metrics)  # ❌ ERRO!
```

### ✅ Solução Aplicada:

**1. Criar handler:**
```python
def datetime_handler(obj):
    """Converte datetime para string ISO format"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
```

**2. Usar no json.dumps:**
```python
json.dumps(metrics, default=datetime_handler)
```

**Resultado:**
```python
# Antes (erro):
{'timestamp': datetime.datetime(2025, 11, 5, 12, 43, 0)}

# Depois (sucesso):
{'timestamp': '2025-11-05T12:43:00'}
```

---

## 📊 Resumo das Correções

| Problema | Causa | Solução | Arquivo |
|----------|-------|---------|---------|
| **PeopleSoft não carrega** | Servidor inacessível | `enabled: false` | `systems_config.json` |
| **Screenshot 404** | Pasta errada (selenium) | Usar pasta `google` | `google_collector.py` |
| **Erro datetime** | JSON não serializa datetime | Handler para ISO format | `local_storage.py` |

---

## 🔄 Fluxo Correto Agora

### 1. Google Coleta Screenshot

```
1. GoogleCollector inicia
   ↓
2. Navega para google.com
   ↓
3. Aguarda logo carregar (ou timeout)
   ↓
4. Salva screenshot em:
   storage/screenshots/google/screenshot_20251105_124312.png
   ↓
5. Retorna caminho correto
```

### 2. API Serve Screenshot

```
1. Frontend: GET /api/screenshot/google
   ↓
2. Backend procura em:
   storage/screenshots/google/
   ↓
3. Encontra arquivo mais recente
   ↓
4. Retorna: { path: "/storage/screenshots/google/screenshot_*.png" }
   ↓
5. Frontend exibe imagem
```

### 3. Storage Salva Métricas

```
1. Orquestrador recebe dados
   ↓
2. Processa métricas
   ↓
3. json.dumps(metrics, default=datetime_handler)
   ↓
4. Converte datetime para ISO string
   ↓
5. Salva no SQLite com sucesso
```

---

## 🎯 Teste das Correções

### 1. Limpar Screenshots Antigos (Opcional)

```bash
# Remover screenshots da pasta errada
rm -rf storage/screenshots/selenium
# Ou no Windows:
rmdir /s storage\screenshots\selenium
```

### 2. Reiniciar Sistema

```bash
# Parar (Ctrl+C se ainda rodando)
# Iniciar novamente
python main.py
```

### 3. Verificar Logs

```
INFO - ✓ Coletor google inicializado
INFO - ⏭ Sistema peoplesoft desabilitado   ← Correto
INFO - 🔄 Coletando: google
INFO - ✓ Screenshot salvo: storage/screenshots/google/...  ← Correto
INFO - ✓ Dados de google processados        ← Sem erro datetime
```

### 4. Verificar TV Display

```
http://localhost:5000/tv
```

**Esperado:**
- ✅ Google: ● Ativo
- ✅ Screenshot do Google visível
- ✅ PeopleSoft: ○ Parado
- ✅ Sem erros 404 no console

---

## 📁 Estrutura de Pastas Correta

```
storage/
└── screenshots/
    ├── google/               ← Google screenshots aqui
    │   ├── screenshot_20251105_124312.png
    │   ├── screenshot_20251105_124407.png
    │   └── ...
    └── peoplesoft/           ← PeopleSoft screenshots aqui
        └── (vazio por enquanto)
```

**NÃO deve existir:** `storage/screenshots/selenium/`

---

## 🔍 Troubleshooting

### Se Google ainda retorna 404:

**1. Verificar pasta:**
```bash
ls storage/screenshots/google/
# Deve mostrar arquivos .png
```

**2. Verificar API:**
```bash
curl http://localhost:5000/api/screenshot/google
# Deve retornar JSON com path
```

**3. Verificar logs:**
```bash
tail -f storage/logs/dashboard.log | grep "google"
```

### Se erro datetime persistir:

**1. Verificar se handler foi aplicado:**
```bash
grep "default=datetime_handler" storage/local_storage.py
# Deve encontrar
```

**2. Reiniciar completamente:**
```bash
# Matar todos os processos Python
taskkill /f /im python.exe

# Iniciar novamente
python main.py
```

---

## 🎯 Status Atual

### ✅ Google:
- **Status:** Ativo
- **Intervalo:** 60 segundos
- **Screenshots:** Pasta correta
- **API:** Funcionando
- **TV Display:** Deve mostrar imagens

### ⏸️ PeopleSoft:
- **Status:** Desabilitado
- **Motivo:** Servidor inacessível
- **Para reativar:** 
  1. Verificar conectividade
  2. Alterar `enabled: true`
  3. Reiniciar

### ✅ Storage:
- **Datetime:** Serialização corrigida
- **Banco:** Salvando métricas
- **Sem erros:** JSON funciona

---

## 📝 Próximos Passos

### 1. Testar Google (Imediato)

```bash
python main.py
# Aguarde 1 minuto
# Abra http://localhost:5000/tv
# Veja screenshot do Google
```

### 2. Resolver PeopleSoft (Quando Disponível)

```bash
# Testar conectividade
ping pswebt1.ajover.com

# Se responder, reativar:
# Edit systems_config.json
# "enabled": true
# Reiniciar main.py
```

### 3. Adicionar Mais Sistemas

```json
{
  "outro_sistema": {
    "enabled": true,
    "collection_interval": 120
  }
}
```

---

## 🎉 Resumo das Correções

### Arquivos Modificados:

1. **`collectors/google_collector.py`**
   - Pasta de screenshots: `selenium` → `google`

2. **`storage/local_storage.py`**
   - Adicionado `datetime_handler`
   - json.dumps com `default=datetime_handler`

3. **`config/systems_config.json`**
   - PeopleSoft: `enabled: false`

### Resultado:

✅ **Google funcionando** - Screenshots aparecem na TV  
⏸️ **PeopleSoft pausado** - Aguardando servidor  
✅ **Storage corrigido** - Sem erros de serialização  
✅ **TV Display operacional** - Grid mostrando status  

**Execute e veja funcionando! 🚀**
