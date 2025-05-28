import re

def validar_sql(query):
    comandos_peligrosos = r'\b(DROP|DELETE\s+FROM\s+\w+\s*(?!WHERE)|TRUNCATE|ALTER)\b'
    if re.search(comandos_peligrosos, query, re.IGNORECASE):
        raise ValueError("Consulta SQL no permitida: contiene comandos peligrosos.")
    return query

def generar_sugerencias(pregunta):
    base_sugerencias = {
        "inmuebles": [
            "¿Cuántos inmuebles hay por ciudad?",
            "¿Cuál es el valor promedio de los inmuebles?",
            "¿Qué inmuebles se vendieron este mes?"
        ],
        "sql": [
            "Dame la consulta SQL para ver las ventas recientes.",
            "Dame la consulta SQL para los inmuebles más caros.",
            "¿Cómo sería una consulta para filtrar por fecha?"
        ]
    }
    if "inmueble" in pregunta.lower():
        return base_sugerencias["inmuebles"]
    elif "sql" in pregunta.lower():
        return base_sugerencias["sql"]
    return ["¿Qué más quieres saber?", "Dame otra consulta."]

def limpiar_datos(datos):
    return [{k: str(v) for k, v in row.items()} for row in datos]