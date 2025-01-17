import cv2
import numpy as np
import time
import paho.mqtt.client as mqtt

THINGSBOARD_HOST = "demo.thingsboard.io"
THINGSBOARD_PATH = "v1/devices/me/telemetry"
ACCESS_TOKEN = "LWrb3Xiwc8WQUDRIVtlW"

MQTT_PORT = 1883
MQTT_KEEP_ALIVE_INTERVAL = 60 #Tiempo de espera en segundos para mantener la conexión activa


# Configurar cliente MQTT
client = mqtt.Client()
client.username_pw_set(ACCESS_TOKEN)
client.connect(THINGSBOARD_HOST, MQTT_PORT, MQTT_KEEP_ALIVE_INTERVAL)
client.loop_start()

# Umbral inicial para considerar que un espacio está ocupado
occupied_threshold = 0.06  # Esto representa el 6% del área del espacio

# Lista de coordenadas de los espacios de estacionamiento
parking_spots = [
    [(99, 34), (201, 171)], #Esquinas superior izquierda (x1, y1) e inferior derecha (x2, y2)
    [(190, 31), (295, 173)],
    [(291, 36), (386, 175)],
    [(394, 36), (479, 177)],
    [(503, 34), (572, 174)],
    [(107, 210), (211, 317)],
    [(206, 208), (280, 311)],
    [(298, 206), (383, 312)],
    [(387, 209), (466, 312)],
    [(476, 209), (548, 314)]
]

# Mapa para asociar números específicos a cada espacio
spot_numbers = {
    0: 101,
    1: 102,
    2: 103,
    3: 104,
    4: 105,
    5: 201,
    6: 202,
    7: 203,
    8: 204,
    9: 205
}

# Mapa para llevar el seguimiento del estado de ocupación de cada espacio
occupancy_counters = {i: 0 for i in range(len(parking_spots))}

# Función para calcular el área de un espacio de estacionamiento
def calculate_area(spot):
    (x1, y1), (x2, y2) = spot
    return abs(x2 - x1) * abs(y2 - y1)

# Función para verificar si el espacio está ocupado usando Canny + Sustracción de fondo
def is_occupied(spot, frame):
    (x1, y1), (x2, y2) = spot

    # Extraer la región de interés (ROI) correspondiente al espacio de estacionamiento
    roi = frame[y1:y2, x1:x2]

    # Convertir a escala de grises
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Aplicar el filtro Gaussiano
    blurred_gray_roi = cv2.GaussianBlur(gray_roi, (5, 5), 0)

    # Aplicar el algoritmo Canny para la detección de bordes
    edges = cv2.Canny(blurred_gray_roi, 100, 150)

    # Calcular el número de píxeles de borde (bordes detectados) en el ROI
    edge_pixels = cv2.countNonZero(edges)

    # Calcular el área total del espacio
    total_area = calculate_area(spot)

    # Calcular el porcentaje de área ocupada por bordes
    occupied_percentage = edge_pixels / total_area

    # Calcular el umbral dinámico basado en el 50% del área del espacio
    dynamic_threshold = total_area * occupied_threshold

    # Si el número de píxeles de borde supera el umbral, el espacio está ocupado
    return occupied_percentage, edge_pixels > dynamic_threshold

# Inicializa la cámara
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("No se puede abrir la cámara")
    exit()

# Comenzar a ejecutar el algoritmo con muestras cada  medio segundo
sampling_interval = 0.5  # Intervalo de medio segundo
last_sample_time = time.time()

# Requiere que el espacio esté ocupado durante 3 muestras consecutivas
required_consecutive_occupancy = 3

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error al capturar el frame")
        break

    # Esperar el intervalo de muestreo
    current_time = time.time()
    if current_time - last_sample_time < sampling_interval:
        continue
    last_sample_time = current_time

    for i, spot in enumerate(parking_spots):
        occupied_percentage, is_spot_occupied = is_occupied(spot, frame)

        if is_spot_occupied:
            # Incrementar el contador si está ocupado
            occupancy_counters[i] += 1
        else:
            # Reiniciar el contador si no está ocupado
            occupancy_counters[i] = 0

        # Si el espacio ha estado ocupado por 3 muestras consecutivas, se considera ocupado
        if occupancy_counters[i] >= required_consecutive_occupancy:
            spot_status = True  # Ocupado
        else:
            spot_status = False  # Disponible

        # Obtener el número asociado al espacio
        spot_number = spot_numbers[i]

        # Publicar un mensaje en ThingsBoard
        telemetry = {
            f"parkingSpot{spot_number}": spot_status
        }
        print("publish: " + telemetry + ", occupied_percentage:" + occupied_percentage)
        client.publish(THINGSBOARD_PATH, payload=str(telemetry), qos=1)

        (x1, y1), (x2, y2) = spot

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()