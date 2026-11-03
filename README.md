# Tono Norteño — prototipo 0.1

Prototipo web gratuito para estimar la tonalidad mayor/menor y una progresión aproximada de acordes a partir de archivos de audio.

## Ejecutarlo en una computadora

Recomendado: Python 3.10 o 3.11.

1. Descomprime la carpeta.
2. Abre una terminal dentro de ella.
3. Crea un entorno e instala dependencias:

   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Inicia la aplicación:

   ```bash
   streamlit run app.py
   ```

5. Abre la dirección local que indique Streamlit.

## Publicarla para usarla desde iPhone

Una opción sencilla es subir estos archivos a un repositorio de GitHub y desplegar el proyecto en Streamlit Community Cloud. La disponibilidad, límites y condiciones del servicio pueden cambiar. No subas canciones protegidas ni archivos privados al repositorio.

## Limitaciones conocidas

- El detector de tonalidad usa perfiles de notas tipo Krumhansl-Schmuckler; puede confundirse con canciones modales, cambios de tono, afinaciones distintas o intros que no reflejan la tonalidad.
- Los acordes se estiman comparando cromas con plantillas sencillas de tríadas. Puede confundir acordes cercanos y no reconoce bien acordes de séptima, inversiones, bajo pedal, adornos ni modulaciones.
- El audio se limita a 5 minutos para evitar un consumo excesivo de recursos.
- La captura directa del micrófono todavía no está implementada. Por ahora graba con el teléfono y sube el archivo.
- La interfaz muestra nombres de notas en español. La grafía de sostenidos/bemoles es simplificada.

## Próximas mejoras

1. Probar con canciones norteñas de tono conocido y corregir manualmente los resultados.
2. Añadir acordes de séptima, inversión y bajo separado.
3. Añadir controles para transponer y mostrar acordes compatibles con el bajo quinto.
4. Incorporar grabación directa desde el navegador.
5. Evaluar un modelo de reconocimiento de acordes más avanzado.
