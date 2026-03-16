import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from fpdf import FPDF
import io
import os

# --- CLASE DE PROCESAMIENTO BIOMECÁNICO ---
class BiomecanicaDashboard:
    def __init__(self):
        # Mapeo de ejes según tu especificación técnica
        self.ejes = {
            'Tilt (X)': 'Angle X(°)',
            'Rotation (Y)': 'Angle Y(°)',
            'Drop (Z)': 'Angle Z(°)'
        }
        # Valores ideales de ROM (grados)
        self.ideales = {'Tilt (X)': 2.0, 'Rotation (Y)': 4.0, 'Drop (Z)': 4.0}

    def calcular_rom(self, df):
        """Calcula el Range of Motion (95-5 percentil)"""
        resultados = {}
        for nombre, col in self.ejes.items():
            if col in df.columns:
                datos_centrados = df[col] - df[col].mean()
                rom = np.percentile(datos_centrados, 95) - np.percentile(datos_centrados, 5)
                resultados[nombre] = round(float(rom), 2)
            else:
                resultados[nombre] = 0.0
        return resultados

    def generar_pdf_bytes(self, df_comparativo):
        """Genera el PDF en memoria y devuelve los bytes (Sin guardar en disco)"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 15, "INFORME BIOMECÁNICO DE ESTABILIDAD PÉLVICA", ln=True, align='C')
        pdf.ln(5)

        # Tabla de Datos
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(230, 230, 230)
        headers = ["Condición", "Eje", "PRE", "POST", "Mejora"]
        for h in headers:
            pdf.cell(38, 10, h, 1, 0, 'C', True)
        pdf.ln()

        pdf.set_font("Arial", '', 9)
        for _, row in df_comparativo.iterrows():
            pdf.cell(38, 8, str(row['Condición']), 1)
            pdf.cell(38, 8, str(row['Parámetro']), 1)
            pdf.cell(38, 8, str(row['PRE']), 1)
            pdf.cell(38, 8, str(row['POST']), 1)
            
            diff = row['Mejora']
            if diff >= 0: pdf.set_text_color(0, 128, 0)
            else: pdf.set_text_color(200, 0, 0)
            pdf.cell(38, 8, str(diff), 1, ln=True)
            pdf.set_text_color(0, 0, 0)

        return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Hip Stability Pro", layout="wide")
st.title("🚴‍♂️ Análisis de Estabilidad de Cadera")
st.write("Sube tus archivos CSV para comparar la cinemática Pre y Post ajuste.")

app = BiomecanicaDashboard()

# Selector de archivos en el lateral
st.sidebar.header("Carga de Datos")
condiciones = ["Llano", "5%", "10%"]
archivos_pre = {}
archivos_post = {}

for c in condiciones:
    archivos_pre[c] = st.sidebar.file_uploader(f"PRE - {c}", type="csv", key=f"pre_{c}")
    archivos_post[c] = st.sidebar.file_uploader(f"POST - {c}", type="csv", key=f"post_{c}")

if st.sidebar.button("Analizar Datos"):
    resultados = {}
    
    # Procesar cada archivo subido
    for c in condiciones:
        # Pre
        if archivos_pre[c]:
            df_pre = pd.read_csv(archivos_pre[c])
            resultados[f"Pre_{c}"] = app.calcular_rom(df_pre)
        else:
            resultados[f"Pre_{c}"] = {k: 0.0 for k in app.ejes.keys()}
        
        # Post
        if archivos_post[c]:
            df_post = pd.read_csv(archivos_post[c])
            resultados[f"Post_{c}"] = app.calcular_rom(df_post)
        else:
            resultados[f"Post_{c}"] = {k: 0.0 for k in app.ejes.keys()}

    # Crear Tabla Comparativa
    lista_tabla = []
    for c in condiciones:
        for eje in app.ejes.keys():
            pre = resultados[f"Pre_{c}"][eje]
            post = resultados[f"Post_{c}"][eje]
            lista_tabla.append({
                "Condición": c, "Parámetro": eje,
                "PRE": pre, "POST": post, "Mejora": round(pre - post, 2)
            })
    
    df_final = pd.DataFrame(lista_tabla)

    # Mostrar Resultados en Streamlit
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Tabla Comparativa (ROM en grados)")
        st.dataframe(df_final, use_container_width=True)
        
        # Botón de descarga de PDF
        pdf_bytes = app.generar_pdf_bytes(df_final)
        st.download_button(
            label="📩 Descargar Informe PDF",
            data=pdf_bytes,
            file_name="Reporte_Estabilidad_Cadera.pdf",
            mime="application/pdf"
        )

    with col2:
        st.subheader("Estado Final vs Ideal")
        categorias = list(app.ideales.keys())
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[resultados["Post_Llano"][c] for c in categorias],
            theta=categorias, fill='toself', name='Post-Fit'
        ))
        fig.add_trace(go.Scatterpolar(
            r=list(app.ideales.values()),
            theta=categorias, name='Rango Ideal', line_dash='dash'
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 8])))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Por favor, sube los archivos CSV en la barra lateral y pulsa 'Analizar Datos'.")
