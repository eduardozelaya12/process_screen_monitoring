#!/usr/bin/env python3
"""Script temporário para inspecionar o banco de dados"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('storage/dashboard.db')
cursor = conn.cursor()

# Listar tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("="*60)
print("TABELAS NO BANCO DE DADOS:")
print("="*60)
for table in tables:
    print(f"  • {table}")

# Contar registros
print("\n" + "="*60)
print("TOTAL DE REGISTROS:")
print("="*60)
cursor.execute('SELECT COUNT(*) FROM metrics')
print(f"  • Métricas: {cursor.fetchone()[0]}")
cursor.execute('SELECT COUNT(*) FROM screenshots')
print(f"  • Screenshots: {cursor.fetchone()[0]}")
cursor.execute('SELECT COUNT(*) FROM events')
print(f"  • Eventos: {cursor.fetchone()[0]}")

# Métricas por sistema
print("\n" + "="*60)
print("MÉTRICAS POR SISTEMA:")
print("="*60)
cursor.execute('SELECT system_name, COUNT(*) as count FROM metrics GROUP BY system_name')
for row in cursor.fetchall():
    print(f"  • {row[0]}: {row[1]} registros")

# Últimas métricas
print("\n" + "="*60)
print("ÚLTIMAS 5 MÉTRICAS COLETADAS:")
print("="*60)
cursor.execute('''
    SELECT system_name, timestamp, total_processes, running, failed, success, 
           success_rate, status 
    FROM metrics 
    ORDER BY timestamp DESC 
    LIMIT 5
''')
for row in cursor.fetchall():
    print(f"\nSistema: {row[0]}")
    print(f"  Timestamp: {row[1]}")
    print(f"  Total Processos: {row[2]}")
    print(f"  Running: {row[3]} | Failed: {row[4]} | Success: {row[5]}")
    print(f"  Taxa de Sucesso: {row[6]}%")
    print(f"  Status: {row[7]}")

# Screenshots
print("\n" + "="*60)
print("ÚLTIMOS SCREENSHOTS:")
print("="*60)
cursor.execute('SELECT system_name, timestamp, file_path FROM screenshots ORDER BY timestamp DESC LIMIT 3')
for row in cursor.fetchall():
    print(f"  • {row[0]} - {row[1]}")
    print(f"    Arquivo: {row[2]}")

conn.close()
print("\n" + "="*60)
