from flask import Flask, request, render_template
import base64
import os
import psycopg2

# Conexión a la base de datos PostgreSQL (Render te da estos datos)

try:
    conn = psycopg2.connect(
    host="dpg-d1i51rmmcj7s73d2i690-a.oregon-postgres.render.com",
    dbname="estacionamiento_db",
    user="estacionamiento_db_user",
    password="kJq0EaoHYH8lk9EJ7TA2SLnT0xdPuJzw",
    port="5432"
)
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")
    raise

cursor = conn.cursor()


app = Flask(__name__)


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
    
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE matricula = %s", (matricula,))
    count = cursor.fetchone()[0]
    if count > 0:
        return {"error": "La matrícula ya está registrada"}, 400
    
    try:
        cursor.execute(
            "INSERT INTO usuario (nombre, apellido_materno, apellido_paterno, color_auto, modelo_auto, matricula, token) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (nombre, apellido_materno, apellido_paterno, color_auto, modelo_auto, matricula, token)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return {"error": f"Error al guardar en la base de datos: {e}"}, 500

    
    return {"token": token}, 200



@app.route("/actualizar_datos", methods=["POST"])
def actualizar_datos():
    data = request.get_json()
    matricula = data.get("matricula")
    if not matricula:
        return {"error": "Matricula requerida"}, 400
    cursor.execute("SELECT * FROM usuarios WHERE matricula = %s", (matricula,))

    row = cursor.fetchone()
    if row:
        # Devuelve todos los datos encontrados
        return {
            "nombre": row[1],
            "apellido_materno": row[2],
            "apellido_paterno": row[3],
            "color_auto": row[4],
            "modelo_auto": row[5],
            "matricula": row[6],
            "token": row[7]
        }, 200
    if not row:
        return {"error": "Matrícula no encontrada"}, 404
    
    token = base64.b64encode(f"u={row[1]}:{matricula}".encode()).decode().rstrip("=")

    cursor.execute(
        "UPDATE usuarios SET nombre = %s, apellido_materno = %s, apellido_paterno = %s, color_auto = %s, modelo_auto = %s, token = %s WHERE matricula = %s",
        (data.get("nombre", row[1]), data.get("apellido_materno", row[2]), data.get("apellido_paterno", row[3]),
        data.get("color_auto", row[4]), data.get("modelo_auto", row[5]), token, matricula)
    )
    
    conn.commit()
    
    return {"mensaje": "Datos actualizados correctamente"}, 200

@app.route("/eliminar_datos", methods=["POST"])
def eliminar_datos():
    data = request.get_json()
    matricula = data.get("matricula")
    if not matricula:
        return {"error": "Matricula requerida"}, 400
    
    cursor.execute("SELECT * FROM usuarios WHERE matricula = %s", (matricula,))
    row = cursor.fetchone()
    if not row:
        return {"error": "Matrícula no encontrada"}, 404
    
    
    cursor.execute("DELETE FROM usuarios WHERE matricula = %s", (matricula,))
    conn.commit()
    
    return {"mensaje": "Datos eliminados correctamente"}, 200

    




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)