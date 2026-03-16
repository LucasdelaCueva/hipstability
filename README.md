# Dashboard de Análisis Biomecánico - Estabilidad de Pelvis

Este proyecto procesa datos procedentes de sensores IMU para analizar la cinemática de la cadera en ciclistas. Compara mediciones **Pre-Fit** y **Post-Fit** en tres condiciones de carga: Llano (0%), 5% y 10% de desnivel.

## 🚲 Ejes de Análisis (Configuración Sacro)
- **Eje X (Pelvic Tilt):** Inclinación Antero-Posterior.
- **Eje Y (Pelvic Rotation/Yaw):** Rotación cenital (desde arriba).
- **Eje Z (Pelvic Drop/Rocking):** Balanceo lateral.

## 📊 Funcionalidades
- **Normalización de datos:** Elimina el offset del sensor para medir oscilación real.
- **Cálculo de ROM:** Rango de movimiento mediante percentiles robustos (95-5).
- **Dashboard Visual:** Gráfica de radar comparando resultados finales contra valores ideales biomecánicos.
- **Informe PDF:** Generación automática de un reporte con tabla comparativa de mejoras.

## 🚀 Instalación
1. Clona el repositorio.
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt