import streamlit as st
import pandas as pd
import json, os

# Carpetas
UPLOAD_FOLDER = 'uploads'
DATA_FOLDER = 'data'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)

minimos_json_path = os.path.join(DATA_FOLDER, 'minimos.json')
existencia_file = os.path.join(UPLOAD_FOLDER, 'existencia_real.xlsx')
resultado_excel = os.path.join(DATA_FOLDER, 'alertas.xlsx')

st.set_page_config(page_title="Monitor de Existencias Reyma", layout="centered")
st.title("📦 Monitor de Existencias Reyma del Sureste")

# 🧭 Instrucciones
with st.expander("🧭 Instrucciones de uso"):
    st.markdown("""
    **1. Cargar archivo `minimos.xlsx`**  
    Formato: columnas `clave`, `descripcion`, `minimo`. Solo vuelve a subirlo si hay cambios.

    **2. Cargar archivo `existencia_real.xlsx`**  
    Se usa la columna número 6 como `"Final Estimado"`.

    **3. Ver Alertas**  
    Aparecerán las claves cuyo stock esté en el mínimo o por debajo.

    **4. Exportar a Excel**  
    Si hay alertas, puedes descargarlas como archivo Excel.

    **5. Limpiar archivo de existencias**  
    Elimina el archivo `existencia_real.xlsx` sin afectar `minimos.json`.
    """)

# 📁 Cargar 'minimos.xlsx'
st.subheader("📁 Cargar archivo de mínimos")
archivo_minimos = st.file_uploader("Sube el archivo minimos.xlsx", type="xlsx")

if archivo_minimos:
    df_minimos = pd.read_excel(archivo_minimos, engine="openpyxl")
    if all(col in df_minimos.columns for col in ['clave', 'descripcion', 'minimo']):
        with open(minimos_json_path, 'w', encoding='utf-8') as f:
            json.dump(df_minimos.to_dict(orient='records'), f, indent=4, ensure_ascii=False)
        st.success("✅ Archivo de mínimos cargado correctamente.")
    else:
        st.error("❌ El archivo no contiene las columnas requeridas: clave, descripcion, minimo.")

# 📥 Cargar 'existencia_real.xlsx'
st.subheader("📥 Cargar archivo de existencia real")
archivo_existencia = st.file_uploader("Sube existencia_real.xlsx", type="xlsx")

if archivo_existencia:
    with open(existencia_file, 'wb') as f:
        f.write(archivo_existencia.getbuffer())
    st.success("📄 Archivo de existencia cargado correctamente.")

# 🧹 Limpiar existencia_real.xlsx
if st.button("🧹 Limpiar archivo de existencia"):
    if os.path.exists(existencia_file):
        os.remove(existencia_file)
        st.success("Archivo de existencia eliminado.")
    else:
        st.warning("No hay archivo de existencia para eliminar.")

# 🚨 Comparar cantidades y mostrar alertas
if os.path.exists(minimos_json_path) and os.path.exists(existencia_file):
    try:
        with open(minimos_json_path, 'r', encoding='utf-8') as f:
            df_minimos = pd.DataFrame(json.load(f))
        df_existencia = pd.read_excel(existencia_file, engine="openpyxl")

        if df_existencia.shape[1] >= 6:
            df_existencia = df_existencia.iloc[:, [0, 5]]
            df_existencia.columns = ['clave', 'cantidad']
            combinado = pd.merge(df_minimos, df_existencia, on='clave')
            alertas = combinado[combinado['cantidad'] <= combinado['minimo']]

            if not alertas.empty:
                st.subheader("🚨 Claves por debajo del mínimo")
                st.dataframe(alertas, height=400)
                alertas.to_excel(resultado_excel, index=False, engine="openpyxl")

                with open(resultado_excel, "rb") as f:
                    st.download_button(
                        label="📥 Descargar resultados en Excel",
                        data=f,
                        file_name="alertas.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.success("🟢 Todas las existencias están por encima del mínimo.")
        else:
            st.error("❌ El archivo existencia_real.xlsx tiene menos de 6 columnas.")
    except Exception as e:
        st.error(f"❌ Error inesperado al comparar: {str(e)}")