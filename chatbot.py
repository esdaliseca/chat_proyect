import requests
from config import HUGGINGFACE_API_TOKEN  # Sin el punto
from db import ejecutar_consulta
from utils import validar_sql, generar_sugerencias, limpiar_datos

def enviar_a_huggingface(pregunta_usuario):
    url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": f"Eres un asistente experto en SQL para la tabla 'trazabilidad_inmuebles' en Azure SQL. Para la pregunta '{pregunta_usuario}', genera una respuesta en formato JSON: {{'intent': 'fetch_data', 'response': 'texto', 'sql': 'query SQL', 'suggestions': ['sugerencia1', 'sugerencia2']}}. Identifica intents: 'fetch_data', 'get_sql', o 'generate_chart'.",
        "parameters": {"max_length": 200, "temperature": 0.7}
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()[0]["generated_text"]
    except requests.exceptions.RequestException as e:
        return f'{{"intent": "fetch_data", "response": "Error con Hugging Face: {str(e)}", "sql": null, "suggestions": []}}'

def procesar_respuesta(contenido):
    import json
    try:
        data = json.loads(contenido)
    except json.JSONDecodeError:
        data = {"intent": "fetch_data", "response": f"Respuesta no válida: {contenido}", "sql": None, "suggestions": []}

    intent = data.get('intent', 'fetch_data')
    sql = data.get('sql')
    response = data.get('response', 'No se encontraron datos')
    suggestions = data.get('suggestions', []) or generar_sugerencias(contenido)

    if sql:
        sql = validar_sql(sql)

    if intent == 'fetch_data' and sql:
        datos = limpiar_datos(ejecutar_consulta(sql))
        return {"respuesta": f"{response}. ¿Te gustaría saber: {', '.join(suggestions)}?", "sql": sql, "datos": datos, "intent": "fetch_data", "suggestions": suggestions}
    elif intent == 'get_sql' and sql:
        return {"respuesta": f"Consulta SQL: {sql}. ¿Te gustaría saber: {', '.join(suggestions)}?", "sql": sql, "datos": None, "intent": "get_sql", "suggestions": suggestions}
    elif intent == 'generate_chart' and sql:
        datos = limpiar_datos(ejecutar_consulta(sql))
        if datos:
            labels = [row.get('label', 'Desconocido') for row in datos]
            values = [float(row.get('value', 0)) for row in datos]
            chart = {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": [{"label": "Datos", "data": values, "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"]}]
                }
            }
            return {"respuesta": f"Gráfico generado. ¿Te gustaría saber: {', '.join(suggestions)}?", "sql": sql, "chart": chart, "datos": datos, "intent": "generate_chart", "suggestions": suggestions}
    return {"respuesta": response, "sql": None, "datos": None, "intent": intent, "suggestions": suggestions}
