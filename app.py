from flask import Flask, request, render_template, jsonify
import base64
import os
import psycopg2
import pandas as pd
from io import BytesIO
from flask import send_file

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


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/registrar")
def show_registrar_form():
    return render_template("registrar_nuevo_usuario.html")

@app.route("/obtener")
def show_obtener_form():
    return render_template("obtener_datos.html")

@app.route("/actualizar")
def show_actualizar_form():
    return render_template("actualizar_datos.html")

@app.route("/eliminar")
def show_eliminar_form():
    return render_template("eliminar_datos.html")

@app.route("/asistencia")
def show_qr_form():
    return render_template("asistencias.html")


@app.route("/registrar_usuario", methods=["POST"])
def registrar_usuario():
    
    data = request.get_json() # Changed to get_json() as frontend sends JSON
    nombre = data.get("nombre")
    apellido_materno = data.get("apellido_materno")
    apellido_paterno = data.get("apellido_paterno")
    color_auto = data.get("color_auto")
    modelo_auto = data.get("modelo_auto")
    matricula = data.get("matricula")
    
    if not all([nombre, apellido_materno, apellido_paterno, color_auto, modelo_auto, matricula]):
        return jsonify({"error": "Faltan datos"}), 400 # Use jsonify for API responses
    
    token = base64.b64encode(f"u={nombre}:{matricula}".encode()).decode().rstrip("=")

    try:
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE matricula = %s", (matricula,))
        count = cursor.fetchone()[0]
        if count > 0:
            return jsonify({"error": "La matrícula ya está registrada"}), 400
        
        
        cursor.execute(
            "INSERT INTO usuarios (nombre, apellido_materno, apellido_paterno, color_auto, modelo_auto, matricula, token) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (nombre, apellido_materno, apellido_paterno, color_auto, modelo_auto, matricula, token)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Error al guardar en la base de datos: {e}"}), 500

    return jsonify({"token": token, "mensaje": "Usuario registrado exitosamente"}), 200




@app.route("/obtener_qr", methods=["POST"])
def obtener_qr():
    data = request.get_json()
    matricula = data.get("matricula")
    if not matricula:
        return jsonify({"error": "Matricula requerida"}), 400
    
    cursor.execute("SELECT token FROM usuarios WHERE matricula = %s", (matricula,))
    row = cursor.fetchone()
    token = row[0] if row else None
    if not row:
        return jsonify({"error": "Matrícula no encontrada"}), 404
    
    return jsonify({
        "token": token,
    }), 200


@app.route("/actualizar_datos", methods=["POST"])
def actualizar_datos():
    data = request.get_json()
    matricula = data.get("matricula")
    if not matricula:
        return jsonify({"error": "Matricula requerida"}), 400
    
    cursor.execute("SELECT * FROM usuarios WHERE matricula = %s", (matricula,))
    row = cursor.fetchone()
    
    if not row:
        return jsonify({"error": "Matrícula no encontrada"}), 404
    
    
    if any(key in data for key in ["nombre", "apellido_materno", "apellido_paterno", "color_auto", "modelo_auto"]):
        
        current_nombre = row[1]
        updated_nombre = data.get("nombre", current_nombre)
        
        token = base64.b64encode(f"u={updated_nombre}:{matricula}".encode()).decode().rstrip("=")

        try:
            cursor.execute(
                "UPDATE usuarios SET nombre = %s, apellido_materno = %s, apellido_paterno = %s, color_auto = %s, modelo_auto = %s, token = %s WHERE matricula = %s",
                (data.get("nombre", row[1]), data.get("apellido_materno", row[2]), data.get("apellido_paterno", row[3]),
                data.get("color_auto", row[4]), data.get("modelo_auto", row[5]), token, matricula)
            )
            conn.commit()
            return jsonify({"mensaje": "Datos actualizados correctamente"}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({"error": f"Error al actualizar en la base de datos: {e}"}), 500
    else:
        
        return jsonify({
            "nombre": row[1],
            "apellido_materno": row[2],
            "apellido_paterno": row[3],
            "color_auto": row[4],
            "modelo_auto": row[5],
            "matricula": row[6],
            "token": row[7]
        }), 200


@app.route("/eliminar_datos", methods=["POST"])
def eliminar_datos():
    data = request.get_json()
    matricula = data.get("matricula")
    if not matricula:
        return jsonify({"error": "Matricula requerida"}), 400
    
    try:
        cursor.execute("SELECT * FROM usuarios WHERE matricula = %s", (matricula,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Matrícula no encontrada"}), 404
        
        cursor.execute("DELETE FROM usuarios WHERE matricula = %s", (matricula,))
        conn.commit()
        return jsonify({"mensaje": "Datos eliminados correctamente"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Error al eliminar de la base de datos: {e}"}), 500

    
@app.route("/obtener_datos", methods=["POST"])
def obtener_datos():
    data = request.get_json()
    matricula = data.get("matricula")
    
    if not matricula:
        return jsonify({"error": "Matricula requerida"}), 400

    try:
        cursor.execute("SELECT * FROM usuarios WHERE matricula = %s ", (matricula,)) 
        rows = cursor.fetchall()
        
        if not rows:
            return jsonify({"mensaje": "No hay datos registrados para esa matrícula"}), 404 
        
        usuario = []
        for row in rows:
            usuario.append({
                "nombre": row[1],
                "apellido_materno": row[2],
                "apellido_paterno": row[3],
                "color_auto": row[4],
                "modelo_auto": row[5],
                "matricula": row[6],
                "token": row[7]
            })
        
        return jsonify({"data_usuario": usuario}), 200
    except Exception as e:
        return jsonify({"error": f"Error al obtener datos de la base de datos: {e}"}), 500

@app.route("/exportar_asistencias", methods=["POST"])
def exportar_asistencias():
    try:
        cursor.execute("SELECT * FROM asistencias")
        rows = cursor.fetchall()
        if not rows:
            return jsonify({"error": "No hay asistencias registradas"}), 404

        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=columns)
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return send_file(
            output,
            download_name="asistencias.xlsx",
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        return jsonify({"error": f"Error al exportar asistencias: {e}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True) 