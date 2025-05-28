import requests
from .config import HUGGINGFACE_API_TOKEN
from .db import ejecutar_consulta
from .utils import validar_sql, generar_sugerencias, limpiar_datos

def enviar_a_huggingface(pregunta_usuario):
    url = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": f"Eres un asistente experto en SQL para la tabla 'trazabilidad_inmuebles' en Azure SQL. Genera SQL queries para preguntas como '{pregunta_usuario}'. Identifica intents: 'fetch_data', 'get_sql', o 'generate_chart'. Responde con JSON: {{'intent': '...', 'response': '...', 'sql': '...', 'suggestions': [...]}}. Incluye 2-3 sugerencias de preguntas relacionadas.",
        "parameters": {"max_length": 200}
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()[0]["generated_text"]

def procesar_respuesta(contenido):
    import json
    try:
        data = json.loads(contenido)
    except json.JSONDecodeError:
        data = {"intent": "fetch_data", "response": "No se pudo procesar la respuesta", "sql": None, "suggestions": []}

    intent = data.get('intent', 'fetch_data')
    sql = data.get('sql')
    response = data.get('response', 'Datos procesados')
    suggestions = data.get('suggestions', []) or generar_sugerencias(contenido)

    if sql:
        sql = validar_sql(sql)

    if intent == 'fetch_data' and sql:
        datos = limpiar_datos(ejecutar_consulta(sql))
        return {"respuesta": f"Datos procesados. ¿Te gustaría saber: {', '.join(suggestions)}?", "sql": sql, "datos": datos, "intent": "fetch_data", "suggestions": suggestions}
    elif intent == 'get_sql' and sql:
        return {"respuesta": f"Aquí está la consulta SQL utilizada: {sql}. ¿Te gustaría saber: {', '.join(suggestions)}?", "sql": sql, "datos": None, "intent": "get_sql", "suggestions": suggestions}
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
    return {"respuesta": response, "sql": None, "datos": None}

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    query = data['queryResult']['queryText']
    hf_response = enviar_a_huggingface(query)
    processed_response = procesar_respuesta(hf_response)
    return jsonify({
        "fulfillmentText": processed_response["respuesta"],
        "payload": processed_response
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)