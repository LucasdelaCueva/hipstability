
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from fpdf import FPDF

# 1. CONFIGURACIÓN INICIAL
# Creamos las carpetas si no existen para evitar errores
os.makedirs('data', exist_ok=True)
os.makedirs('output', exist_ok=True)

class BiomecanicaDashboard:
    def __init__(self):
        # Mapeo de ejes según tu especificación técnica
        self.ejes = {
            'Tilt (X)': 'Angle X(°)',
            'Rotation (Y)': 'Angle Y(°)',
            'Drop (Z)': 'Angle Z(°)'
        }
        # Valores ideales de ROM (grados) basados en manuales RFEC Nivel II/III
        self.ideales = {
            'Tilt (X)': 2.0, 
            'Rotation (Y)': 4.0, 
            'Drop (Z)': 4.0
        }

    def calcular_rom(self, file_path):
        """Lee el CSV y calcula el Rango de Movimiento (ROM)"""
        if not os.path.exists(file_path):
            print(f"⚠️ Archivo no encontrado: {file_path}. Saltando...")
            return {k: 0.0 for k in self.ejes.keys()}
        
        try:
            df = pd.read_csv(file_path, skipinitialspace=True)
            resultados = {}
            for nombre, col in self.ejes.items():
                # Normalizamos restando la media para medir solo la oscilación
                datos_centrados = df[col] - df[col].mean()
                # Usamos percentiles 5 y 95 para eliminar picos de ruido del sensor
                rom = np.percentile(datos_centrados, 95) - np.percentile(datos_centrados, 5)
                resultados[nombre] = round(float(rom), 2)
            return resultados
        except Exception as e:
            print(f"❌ Error procesando {file_path}: {e}")
            return {k: 0.0 for k in self.ejes.keys()}

    def generar_reporte_pdf(self, df_comparativo, radar_path, nombre_archivo):
        """Crea un PDF profesional con los resultados"""
        pdf = FPDF()
        pdf.add_page()
        
        # Título
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 15, "INFORME BIOMECÁNICO DE ESTABILIDAD PÉLVICA", ln=True, align='C')
        pdf.ln(5)

        # Tabla de Datos
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(230, 230, 230)
        headers = ["Condición", "Eje", "PRE", "POST", "Mejora"]
        for h in headers:
            pdf.cell(38, 10, h, 1, 0, 'C', True)
        pdf.ln()

        pdf.set_font("Arial", '', 10)
        for _, row in df_comparativo.iterrows():
            pdf.cell(38, 9, str(row['Condición']), 1)
            pdf.cell(38, 9, str(row['Parámetro']), 1)
            pdf.cell(38, 9, str(row['PRE']), 1)
            pdf.cell(38, 9, str(row['POST']), 1)
            
            # Color verde si mejora (ROM baja), rojo si empeora
            diff = row['Mejora']
            if diff >= 0:
                pdf.set_text_color(0, 128, 0) # Verde
            else:
                pdf.set_text_color(200, 0, 0) # Rojo
            pdf.cell(38, 9, str(diff), 1, ln=True)
            pdf.set_text_color(0, 0, 0)

        # Gráfico de Radar
        if os.path.exists(radar_path):
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Estado Final (Llano) vs Rango Ideal", ln=True)
            pdf.image(radar_path, x=20, w=170)

        pdf.output(nombre_archivo)
        print(f"✅ PDF generado con éxito: {nombre_archivo}")

# --- BLOQUE DE EJECUCIÓN ---
if __name__ == "__main__":
    app = BiomecanicaDashboard()

    # Definimos los nombres de archivos que deben estar en la carpeta /data
    archivos = {
        "Pre_Llano": "data/pre_llano.csv", "Pre_5%": "data/pre_5.csv", "Pre_10%": "data/pre_10.csv",
        "Post_Llano": "data/post_llano.csv", "Post_5%": "data/post_5.csv", "Post_10%": "data/post_10.csv"
    }

    # 2. PROCESAR DATOS
    resultados_finales = {k: app.calcular_rom(v) for k, v in archivos.items()}

    # 3. CREAR TABLA COMPARATIVA
    lista_tabla = []
    for cond, label in [("Llano", "Llano"), ("5%", "Subida 5%"), ("10%", "Subida 10%")]:
        for eje in app.ejes.keys():
            pre = resultados_finales[f"Pre_{cond}"][eje]
            post = resultados_finales[f"Post_{cond}"][eje]
            lista_tabla.append({
                "Condición": label,
                "Parámetro": eje,
                "PRE": pre,
                "POST": post,
                "Mejora": round(pre - post, 2)
            })
    
    df_final = pd.DataFrame(lista_tabla)

    # 4. GENERAR GRÁFICA DE RADAR (POST LLANO)
    categorias = list(app.ideales.keys())
    fig = go.Figure()
    
    # Datos actuales
    fig.add_trace(go.Scatterpolar(
        r=[resultados_finales["Post_Llano"][c] for c in categorias],
        theta=categorias, fill='toself', name='Post-Fit'
    ))
    # Referencia ideal
    fig.add_trace(go.Scatterpolar(
        r=list(app.ideales.values()),
        theta=categorias, name='Rango Ideal', line_dash='dash'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 8])),
        title="Estabilidad Final vs Ideal (Menos es mejor)"
    )
    
    # Guardar imagen temporal para el PDF
    radar_img = "output/radar_temp.png"
    fig.write_image(radar_img)

    # 5. EXPORTAR PDF FINAL
    app.generar_reporte_pdf(df_final, radar_img, "output/Reporte_Biomecanico.pdf")
