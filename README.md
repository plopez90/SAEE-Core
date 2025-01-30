# SAEE-Core
 
_Sistema Avanzado para Estacionamientos Eficientes_

Este repositorio contiene el código del módulo core de SAEE, encargado de detectar si un espacio de estacionamiento está ocupado o libre mediante procesamiento de imágenes y enviar los resultados a la thingsboard a través de MQTT.

## Estructura del Proyecto

El proyecto consta de los siguientes archivos principales:

### 1. `reference_image_generator.py`
Este script toma una imagen de referencia y superpone marcas visuales para que puedas identificar puntos de interés en la imagen. Estos puntos `(x, y)` se utilizarán luego para definir las áreas de los espacios de estacionamiento en `parking_detection.py`.

#### Uso:
1. Ejecuta el script `reference_image_generator.py`.
2. La imagen resultante tendrá referencias visuales para tomar coordenadas de los espacios de estacionamiento.
3. Selecciona 4 puntos por espacio y agrégalos en `parking_detection.py` en el formato:
   ```python
   [(61, 67), (210, 61), (234, 262), (103, 276)]
   ```
   **Orden de los puntos:**
   - Esquina superior izquierda
   - Esquina superior derecha
   - Esquina inferior derecha
   - Esquina inferior izquierda

### 2. `parking_detection.py`
Este script se encarga de capturar video en tiempo real, analizar los espacios de estacionamiento definidos y detectar si están ocupados o libres. Luego, envía esta información a una plataforma thingsboard mediante MQTT.

#### Uso:
1. Completa los espacios de estacionamiento con los puntos obtenidos de `reference_image_generator.py`.
2. Ejecuta `parking_detection.py`. La detección comenzará automáticamente y enviará los datos a la plataforma thingsboard.

## Configuración MQTT
El script `parking_detection.py` está configurado para enviar datos a ThingsBoard u otra plataforma MQTT. Asegúrate de configurar:
- `THINGSBOARD_HOST`
- `ACCESS_TOKEN`
- `MQTT_PORT`

## Requisitos
- Python 3
- OpenCV
- NumPy
- Paho MQTT

Para instalar las dependencias, ejecuta:
```bash
pip install opencv-python numpy paho-mqtt
```

## Ejecución
1. Genera la imagen de referencia:
   ```bash
   python reference_image_generator.py
   ```
2. Obtén los puntos de referencia y agrégalos en `parking_detection.py`.
3. Ejecuta la detección:
   ```bash
   python parking_detection.py
   ```

