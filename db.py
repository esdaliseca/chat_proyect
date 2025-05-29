import pyodbc
from config import AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_USER, AZURE_SQL_PASSWORD, AZURE_SQL_DRIVER  # Sin el punto

def conectar_bd():
    conn_str = f"DRIVER={AZURE_SQL_DRIVER};SERVER={AZURE_SQL_SERVER};DATABASE={AZURE_SQL_DATABASE};UID={AZURE_SQL_USER};Pwd={AZURE_SQL_PASSWORD}"
    return pyodbc.connect(conn_str)

def ejecutar_consulta(sql_query):
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        columnas = [column[0] for column in cursor.description]
        resultados = [dict(zip(columnas, row)) for row in cursor.fetchall()]
        conn.close()
        return resultados
    except Exception as e:
        return [{"error": str(e)}]
