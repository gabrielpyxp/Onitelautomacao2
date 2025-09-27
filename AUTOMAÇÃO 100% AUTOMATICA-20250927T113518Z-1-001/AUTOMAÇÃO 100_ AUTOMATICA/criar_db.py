import pandas as pd
import sqlite3
import re
from datetime import datetime

def clean_sla(value):
    """Converte valores de SLA para números"""
    try:
        if pd.isna(value):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = re.sub(r'[^\d.,-]', '', str(value))
        cleaned = cleaned.replace(',', '.')
        return float(cleaned)
    except:
        return None

def main():
    try:
        df = pd.read_excel('downloads/resultado.xlsx')
        
        # Selecionar e renomear colunas
        df = df.rename(columns={
            'Cliente': 'NomeCliente',
            'SLA': 'SLA',
            'Abertura': 'Abertura',
            'Status': 'Status'
        })[['ID', 'NomeCliente', 'SLA', 'Abertura', 'Status']]
        
        # Converter dados
        df['SLA'] = df['SLA'].apply(clean_sla)
        df['Abertura'] = pd.to_datetime(df['Abertura']).dt.strftime('%Y-%m-%d %H:%M:%S')
        df = df.dropna()
        
        # Conectar ao banco
        conn = sqlite3.connect('relatorios.db')
        
        # Verificar se a tabela existe
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='relatorios'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Atualização incremental - remove registros existentes
            existing_ids = pd.read_sql("SELECT ID FROM relatorios", conn)['ID'].tolist()
            df = df[~df['ID'].isin(existing_ids)]
        
        # Salvar no banco
        df.to_sql('relatorios', conn, if_exists='append', index=False)
        conn.close()
        
        print(f"✅ Dados atualizados: {len(df)} novos registros")
        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar banco de dados: {str(e)}")
        return False

if __name__ == '__main__':
    main()