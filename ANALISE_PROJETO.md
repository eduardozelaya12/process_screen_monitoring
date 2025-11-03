# 📊 ANÁLISE COMPLETA DO PROJETO - Process Monitor Dashboard

## 📋 Visão Geral

Este é um **sistema de monitoramento automatizado** para processos PeopleSoft (e outros sistemas ERP). Ele captura screenshots periodicamente e extrai métricas dos processos em execução.

---

## 🏗️ Arquitetura do Sistema

### Componentes Principais:

```
┌─────────────────────────────────────────────────────────────┐
│                         MAIN.PY                             │
│  (Ponto de entrada - Inicia todos os componentes)          │
└────────┬─────────────────────────────────┬──────────────────┘
         │                                 │
         ▼                                 ▼
┌────────────────────┐           ┌─────────────────────┐
│   ORCHESTRATOR     │           │   BACKEND (Flask)   │
│  (Coordenador)     │◄─────────►│   + SocketIO        │
└─────────┬──────────┘           └──────────┬──────────┘
          │                                  │
          │ Agenda Jobs                      │ API REST
          │                                  │ WebSocket
          ▼                                  │
┌─────────────────────┐                     │
│    COLLECTORS       │                     │
│  - PeopleSoft       │                     │
│  - (Outros...)      │                     │
└─────────┬───────────┘                     │
          │                                  │
          │ Coleta dados                     │
          ▼                                  │
┌─────────────────────┐                     │
│    PROCESSORS       │                     │
│  (Padroniza dados)  │                     │
└─────────┬───────────┘                     │
          │                                  │
          │ Dados processados                │
          ▼                                  ▼
┌──────────────────────────────────────────────┐
│           STORAGE (SQLite)                   │
│  - Tabela: metrics                           │
│  - Tabela: screenshots                       │
│  - Tabela: events                            │
└──────────────────────────────────────────────┘
          │
          │ Armazena                          
          ▼                                  
┌──────────────────────┐          ┌──────────────────┐
│  Screenshots (PNG)   │          │  FRONTEND (HTML) │
│  /storage/           │          │  - Dashboard     │
└──────────────────────┘          │  - TV Display    │
                                  └──────────────────┘
```

---

## 🔄 Fluxo de Funcionamento

### 1. **Inicialização (main.py)**
   - Cria diretórios necessários
   - Inicia o **Orchestrator** em thread separada
   - Inicia o **servidor Flask** na thread principal
   - Disponibiliza em: `http://localhost:5000`

### 2. **Orchestrator (orchestrator.py)**
   - Carrega configuração de `config/systems_config.json`
   - Inicializa coletores para cada sistema habilitado
   - Agenda jobs periódicos usando **APScheduler**
   - Coleta dados a cada X segundos (configurável, padrão: 300s)

### 3. **Coletor PeopleSoft (peoplesoft_collector.py)**
   O coletor realiza estas etapas:
   
   #### a) Autenticação
   - Verifica se há cookies salvos em `config/credentials/peoplesoft_cookies.pkl`
   - Se não há cookies ou estão expirados, faz login:
     * Abre Chrome via Selenium
     * Preenche credenciais (username/password)
     * Salva cookies para próximas execuções
   
   #### b) Captura de Dados
   - Carrega cookies salvos
   - Navega para URL do Process Monitor
   - Verifica se está na página correta (sanity check)
   - Limpa filtros de nome e clica em "Refresh"
   - Extrai métricas da tabela de processos
   
   #### c) Extração de Métricas
   Procura a tabela de processos usando múltiplos seletores:
   - `table[id*='PROCESS']`
   - `table.PSLEVEL1GRID`
   - `table.PSLEVEL1GRIDWBO`
   
   Para cada linha, identifica:
   - **Total de processos**
   - **Running**: processos em execução
   - **Failed**: processos com erro
   - **Success**: processos concluídos com sucesso
   - **Success Rate**: taxa de sucesso (%)
   
   #### d) Screenshot
   - Captura screenshot da página inteira
   - Salva em: `storage/screenshots/peoplesoft/screenshot_TIMESTAMP.png`

### 4. **Armazenamento (local_storage.py)**
   Salva no SQLite (`storage/dashboard.db`):
   
   **Tabela `metrics`:**
   - system_name (ex: "peoplesoft")
   - timestamp
   - total_processes
   - running, failed, success
   - success_rate
   - status ("healthy", "error", "warning")
   - data (JSON completo)

### 5. **Backend API (routes.py)**
   Endpoints REST:
   - `GET /` → Dashboard principal
   - `GET /tv` → Versão para TV
   - `GET /api/status` → Status de todos os sistemas
   - `GET /api/status/<sistema>` → Status de um sistema
   - `GET /api/history/<sistema>` → Histórico de métricas
   - `GET /api/screenshot/<sistema>` → Último screenshot

### 6. **WebSocket (websocket_handlers.py)**
   Comunicação em tempo real:
   - Clientes se conectam via SocketIO
   - Recebem updates automáticos quando há nova coleta
   - Podem solicitar updates sob demanda
   - Sistema de "rooms" para filtrar por sistema

---

## 📊 Estado Atual do Banco de Dados

### Resumo:
```
TABELAS:
  • metrics       → 19 registros
  • screenshots   → 0 registros  
  • events        → 0 registros

SISTEMA MONITORADO:
  • peoplesoft: 19 coletas realizadas

ÚLTIMAS COLETAS:
  1. 16:35:21 - Total: 0 processos (status: healthy)
  2. 16:32:12 - Total: 0 processos (status: healthy)
  3. 16:13:35 - Total: 0 processos (status: healthy)
  4. 16:00:48 - Total: 0 processos (status: healthy)
  5. 15:54:49 - Total: 0 processos (status: ERROR)
```

### Screenshots Salvos:
```
storage/screenshots/peoplesoft/
  • screenshot_20251103_161329.png (17 KB)
  • screenshot_20251103_163205.png (19 KB)
  • screenshot_20251103_163514.png (19 KB)
```

---

## ⚠️ PROBLEMAS IDENTIFICADOS

### 1. **Tabela de processos não está sendo encontrada**
   **Sintoma:** Todas as métricas mostram "0 processos"
   
   **Possíveis causas:**
   - ✗ Seletores CSS não estão localizando a tabela correta
   - ✗ Página pode estar em um iframe que não foi acessado
   - ✗ Tabela pode ter um ID/classe diferente do esperado
   - ✗ Página pode estar vazia (sem processos)

   **Evidências no código:**
   ```python
   # Linha 390-405: peoplesoft_collector.py
   # Tenta fazer switch para frame 'ptifrmtgtframe'
   # mas pode não estar funcionando corretamente
   ```

### 2. **Screenshots não estão sendo registrados no banco**
   - Screenshots são salvos no disco (3 arquivos encontrados)
   - Mas a tabela `screenshots` está vazia
   - Falta implementar a gravação no banco

### 3. **Redirecionamento para login detectado**
   O código tem proteção contra redirecionamento (linhas 204-255):
   - Verifica se foi redirecionado para tela de login
   - Tenta fazer relogin automático
   - Mas pode estar falhando silenciosamente

---

## 🔍 O que está NO PRINT da imagem

A imagem mostra o **Dashboard Web** com:
- Título: "Process Monitor Dashboard"
- Seção: "Último Screenshot (PeopleSoft ou Fallback)"
- **Screenshot exibido**: parece ser uma tela do PeopleSoft

Isso confirma que:
1. ✓ O frontend está funcionando
2. ✓ Screenshots estão sendo capturados
3. ✓ Backend está servindo os arquivos
4. ✗ **MAS** as métricas não estão sendo extraídas (0 processos)

---

## 🛠️ DEBUG RECOMENDADO

### 1. Verificar HTML da página
O código salva o HTML em caso de erro:
```
storage/logs/page_structure.html
storage/logs/page_structure_wrong_url.html
```

### 2. Verificar screenshot de erro
```
storage/logs/screenshot_wrong_url.png
storage/logs/login_error.png
```

### 3. Verificar logs detalhados
```python
# Ver linha 152-198 do peoplesoft_collector.py
# Logs mostram:
# - URL atual após navegação
# - Se host está correto
# - Se path está correto
# - Frames disponíveis
```

### 4. Teste manual
Execute o script de teste:
```bash
python test_peoplesoft.py
```

---

## 📝 Próximos Passos Sugeridos

1. **Analisar o HTML salvo** para identificar a estrutura real da tabela
2. **Ajustar seletores CSS** baseado na estrutura real
3. **Implementar gravação de screenshots no banco**
4. **Adicionar mais logs** durante a extração
5. **Considerar usar XPath** ao invés de CSS selectors

---

## 🎯 Conclusão

O sistema está **funcionando parcialmente**:
- ✓ Arquitetura completa e bem estruturada
- ✓ Scheduler funcionando (19 coletas realizadas)
- ✓ Screenshots sendo capturados
- ✓ Frontend exibindo dados
- ✓ WebSocket configurado
- ✗ **Extração de métricas não está funcionando**

O problema principal está na **localização da tabela de processos** dentro da página PeopleSoft.
