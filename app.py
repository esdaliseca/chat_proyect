from flask import Flask, request, jsonify, render_template
from .chatbot import enviar_a_huggingface, procesar_respuesta
from flask_cors import CORS

app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend/templates')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def preguntar():
    data = request.get_json()
    pregunta = data.get('queryResult', {}).get('queryText') or data.get('pregunta')

    if not pregunta:
        return jsonify({"fulfillmentText": "La pregunta es obligatoria", "payload": {"error": "La pregunta es obligatoria"}}), 400

    try:
        respuesta_modelo = enviar_a_huggingface(pregunta)
        resultado = procesar_respuesta(respuesta_modelo)

        if resultado.get('intent') == 'get_sql' and pregunta.lower().startswith('dame la consulta'):
            return jsonify({
                "fulfillmentText": resultado['respuesta'],
                "payload": {"sql_query": resultado['sql'], "suggestions": resultado.get('suggestions', [])}
            })
        elif resultado.get('intent') == 'generate_chart' and 'genera' in pregunta.lower():
            chart_data = resultado.get('chart', {"type": "bar", "data": {"labels": ["Error"], "datasets": [{"label": "Datos", "data": [0], "backgroundColor": ["#FF6384"]}]}})
            return jsonify({
                "fulfillmentText": resultado['respuesta'],
                "payload": {"response": resultado['respuesta'], "chart_data": chart_data, "suggestions": resultado.get('suggestions', [])}
            })
        return jsonify({
            "fulfillmentText": resultado['respuesta'],
            "payload": {
                "response": resultado['respuesta'],
                "sql": resultado.get('sql'),
                "datos": resultado.get('datos'),
                "suggestions": resultado.get('suggestions', [])
            }
        })
    except Exception as e:
        return jsonify({"fulfillmentText": f"Error: {str(e)}", "payload": {"error": str(e)}}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    print("🔄 Iniciando aplicación...")
