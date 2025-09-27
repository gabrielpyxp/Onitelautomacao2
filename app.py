from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
LAST_UPDATE = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
def index():
    return render_template('index.html', last_update=LAST_UPDATE)

@app.route('/api/data')
def get_data():
    conn = sqlite3.connect('relatorios.db')
    conn.row_factory = sqlite3.Row
    
    # Obter parâmetros de filtro
    sla_filter = request.args.get('sla_filter')
    
    # Construir consulta base
    query = "SELECT ID, NomeCliente, SLA, Abertura, Status FROM relatorios ORDER BY Abertura DESC"
    params = []
    
    # Aplicar filtros
    if sla_filter == "positivo":
        query += " WHERE SLA >= 90"
    elif sla_filter == "negativo":
        query += " WHERE SLA < 90"
    
    # Executar consulta
    cursor = conn.execute(query, params)
    dados = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'data': [dict(row) for row in dados],
        'last_update': LAST_UPDATE
    })

def update_last_update():
    global LAST_UPDATE
    LAST_UPDATE = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    app.run(debug=False)