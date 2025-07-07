from flask import Flask, request, render_template
import base64
import os

app = Flask(__name__)
datos_temporales = []

@app.route("/guardar_datos", methods=["POST"])
def guardar_datos():
    # Obetern datos del formulario
    data = request.get_json()
    nombre = data.get("nombre")
    apellido_materno = data.get("apellido_materno")
    apellido_paterno = data.get("apellido_paterno")
    color_auto = data.get("color_auto")
    modelo_auto = data.get("modelo_auto")
    matricula = data.get("matricula")
    token = base64.b64encode(f"u={nombre}:{matricula}".encode()).decode().rstrip("=")
    if not all([nombre, apellido_materno, apellido_paterno, color_auto, modelo_auto, matricula, token]):
        return {"error": "Faltan datos"}, 400
    # Guardar datos en la lista temporal
    datos_temporales.append({
        "nombre": nombre,
        "apellido_materno": apellido_materno,
        "apellido_paterno": apellido_paterno,
        "color_auto": color_auto,
        "modelo_auto": modelo_auto,
        "matricula": matricula,
        "token": token
    })
    return {"message": "Datos guardados correctamente", "token": token}, 200

@app.route("/obtener_datos", methods=["GET"])
def obtener_datos():
    respuesta = datos_temporales.copy()
    datos_temporales.clear()  # Limpiar datos temporales después de obtenerlos
    return {"datos": respuesta}, 200



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
