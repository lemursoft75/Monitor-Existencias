from flask import Flask, request, render_template, redirect, send_file
import pandas as pd
import json, os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
DATA_FOLDER = 'data'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

minimos_json_path = os.path.join(DATA_FOLDER, 'minimos.json')
existencia_file = os.path.join(UPLOAD_FOLDER, 'existencia_real.xlsx')
resultado_excel = os.path.join(DATA_FOLDER, 'alertas.xlsx')

@app.route('/', methods=['GET', 'POST'])
def monitor_existencias():
    alertas = []
    mensaje_success = None
    mensaje_error = None

    if request.method == 'POST':
        archivo = request.files.get('archivo')
        accion = request.form.get('accion')

        # Acción: limpiar solo existencia
        if accion == 'limpiar':
            if os.path.exists(existencia_file):
                os.remove(existencia_file)
            mensaje_success = "🧹 Archivo de existencia eliminado. Los mínimos permanecen guardados."
            return render_template("inventario.html", productos=[], mensaje_success=mensaje_success)

        # Acción: exportar a Excel
        elif accion == 'exportar':
            if os.path.exists(resultado_excel):
                return send_file(resultado_excel, as_attachment=True)
            else:
                mensaje_error = "❌ No hay resultados para exportar."
                return render_template("inventario.html", productos=[], mensaje_error=mensaje_error)

        # Acción: subir archivo
        elif archivo:
            nombre = archivo.filename.lower()
            if 'minimos' in nombre and archivo.filename.endswith('.xlsx'):
                df_minimos = pd.read_excel(archivo)
                if all(col in df_minimos.columns for col in ['clave', 'descripcion', 'minimo']):
                    minimos_dict = df_minimos.to_dict(orient='records')
                    with open(minimos_json_path, 'w', encoding='utf-8') as f:
                        json.dump(minimos_dict, f, indent=4, ensure_ascii=False)
                    mensaje_success = "✅ Archivo 'minimos' cargado correctamente."
                else:
                    mensaje_error = "❌ Error: El archivo 'minimos.xlsx' no contiene las columnas requeridas."
                return render_template("inventario.html", productos=alertas, mensaje_success=mensaje_success, mensaje_error=mensaje_error)

            elif 'existencia' in nombre and archivo.filename.endswith('.xlsx'):
                archivo.save(existencia_file)
                return redirect('/')

    # Comparación si ambos existen
    if os.path.exists(minimos_json_path) and os.path.exists(existencia_file):
        try:
            with open(minimos_json_path, 'r', encoding='utf-8') as f:
                minimos_df = pd.DataFrame(json.load(f))
            existencia = pd.read_excel(existencia_file)

            if existencia.shape[1] >= 6:
                existencia = existencia.iloc[:, [0, 5]]
                existencia.columns = ['clave', 'cantidad']
                combinado = pd.merge(minimos_df, existencia, on='clave')
                resultado_df = combinado[combinado['cantidad'] <= combinado['minimo']]
                alertas = resultado_df.to_dict(orient='records')

                # Guardar resultado como Excel
                if not resultado_df.empty:
                    resultado_df.to_excel(resultado_excel, index=False)
            else:
                mensaje_error = "❌ Error: El archivo 'existencia_real.xlsx' no contiene al menos 6 columnas."
        except Exception as e:
            mensaje_error = f"❌ Error inesperado: {str(e)}"

    return render_template("inventario.html", productos=alertas, mensaje_success=mensaje_success, mensaje_error=mensaje_error)

if __name__ == '__main__':
    app.run(debug=True)