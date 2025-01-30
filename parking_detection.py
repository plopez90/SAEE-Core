import cv2
import numpy as np
import paho.mqtt.client as mqtt
import time

class Config:
    THINGSBOARD_HOST = "demo.thingsboard.io"
    THINGSBOARD_PATH = "v1/devices/me/telemetry"
    ACCESS_TOKEN = "LWrb3Xiwc8WQUDRIVtlW"
    MQTT_PORT = 1883
    MQTT_KEEP_ALIVE_INTERVAL = 60
    OCCUPIED_THRESHOLD = 0.06  # # Umbral para considerar un espacio ocupado (6% del área del espacio)
    SAMPLING_INTERVAL = 1  # Intervalo de muestreo en segundos
    REQUIRED_CONSECUTIVE_OCCUPANCY = 3  # Pasadas consecutivas para confirmar ocupación

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.username_pw_set(Config.ACCESS_TOKEN)
        try:
            self.client.connect(Config.THINGSBOARD_HOST, Config.MQTT_PORT, Config.MQTT_KEEP_ALIVE_INTERVAL)
            self.client.loop_start()
            print("Conexión MQTT exitosa")
        except Exception as e:
            print(f"Error al conectar con MQTT: {e}")

    def publish(self, topic, telemetry, occupied_percentage):
        try:
            print(f"Publicando estado: {telemetry}, Porcentage ocupado: {occupied_percentage:.2%}")
            self.client.publish(topic, payload=str(telemetry), qos=1)
        except Exception as e:
            print(f"Error al publicar en MQTT: {e}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

class ParkingSpotDetector:
    def __init__(self, mqtt_client):
        self.mqtt_client = mqtt_client
        self.parking_spots = self.define_parking_spots()
        self.spot_numbers = self.define_spot_numbers()

        # Mapa para llevar el seguimiento del estado de ocupación de cada espacio
        self.occupancy_counters = {i: 0 for i in range(len(self.parking_spots))}

        # Estado actual de cada lugar
        self.occupancy_status = {i: False for i in range(len(self.parking_spots))}

        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            print("No se puede abrir la cámara")
            exit()
        self.initialize_state()

    # Coordenadas de los espacios de estacionamiento
    def define_parking_spots(self):
        return [
            [(61, 67), (210, 61), (234, 262), (103, 276)],  # Polígono rectangular (Esquina superior izquierda, Esquina superior derecha, Esquina inferior derecha, Esquina inferior izquierda)
            [(275, 62), (414, 61), (439, 259), (300, 268)],
            [(483, 52), (629, 47), (633, 252), (494, 260)],
            [(682, 42), (853, 37), (846, 253), (685, 262)],
            [(295, 344), (438, 342), (458, 524), (314, 527)],
            [(108, 344), (256, 338), (269, 509), (138, 525)],
            [(483, 334), (637, 331), (635, 508), (501, 512)],
            [(678, 336), (839, 327), (833, 499), (684, 502)]
        ]
    
    # Mapa para asociar números específicos a cada espacio
    def define_spot_numbers(self):
        return {
            0: 101,
            1: 102,
            2: 103,
            3: 104,
            4: 105,
            5: 201,
            6: 202,
            7: 203
        }

    def calculate_area(self, polygon):
        return cv2.contourArea(np.array(polygon, dtype=np.int32))

    def is_occupied(self, polygon, frame):
        # Crear una máscara en blanco
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        points = np.array(polygon, dtype=np.int32)

        # Rellenar el polígono del ROI en la máscara
        cv2.fillPoly(mask, [points], 255)

        # Extraer la región de interés (ROI) correspondiente al espacio de estacionamiento
        roi = cv2.bitwise_and(frame, frame, mask=mask)

        # Convertir a escala de grises
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # Aplicar el filtro Gaussiano
        blurred_gray_roi = cv2.GaussianBlur(gray_roi, (5, 5), 0)

        # Aplicar el algoritmo Canny para la detección de bordes
        edges = cv2.Canny(blurred_gray_roi, 75, 125)

        # Filtrar únicamente los bordes dentro del ROI (aplicando la máscara)
        edges_within_roi = cv2.bitwise_and(edges, edges, mask=mask)

        # Calcular el número de píxeles de borde (bordes detectados) en el ROI
        edge_pixels = cv2.countNonZero(edges_within_roi)

        # Calcular el área total del espacio (ROI)
        total_area = self.calculate_area(polygon)

        # Calcular el porcentaje de área ocupada por bordes
        occupied_percentage = edge_pixels / total_area

        # Calcular el umbral
        area_based_threshold = total_area * Config.OCCUPIED_THRESHOLD

        # Si el número de píxeles de borde supera el umbral, el espacio está ocupado
        return occupied_percentage, edge_pixels > area_based_threshold

    # Publicar estado inicial de cada lugar
    def initialize_state(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Error al capturar el frame inicial")
            exit()
        
        for i, spot in enumerate(self.parking_spots):
            occupied_percentage, is_spot_occupied = self.is_occupied(spot, frame)
            self.occupancy_status[i] = is_spot_occupied
            telemetry = {f"parkingSpot{self.spot_numbers[i]}": is_spot_occupied}
            self.mqtt_client.publish(Config.THINGSBOARD_PATH, telemetry, occupied_percentage)

    def run(self):
        last_sample_time = time.time()
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Error al capturar el frame")
                break
            
            # Esperar el intervalo de muestreo
            current_time = time.time()
            if current_time - last_sample_time < Config.SAMPLING_INTERVAL:
                continue
            last_sample_time = current_time

            for i, spot in enumerate(self.parking_spots):
                occupied_percentage, is_spot_occupied = self.is_occupied(spot, frame)

                if is_spot_occupied:
                    self.occupancy_counters[i] += 1 # Incrementar el contador si está ocupado
                else:
                    self.occupancy_counters[i] = 0  # Reiniciar contador si no está ocupado

                # Se actualiza el estado solo si ha sido consistente por 3 pasadas consecutivas
                if self.occupancy_counters[i] >= Config.REQUIRED_CONSECUTIVE_OCCUPANCY:
                    if not self.occupancy_status[i]:  # Solo publicar si el estado cambia
                        self.occupancy_status[i] = True
                        telemetry = {f"parkingSpot{self.spot_numbers[i]}": True}
                        self.mqtt_client.publish(Config.THINGSBOARD_PATH, telemetry, occupied_percentage)
                else:
                    if self.occupancy_status[i]:  # Solo publicar si el estado cambia
                        self.occupancy_status[i] = False
                        telemetry = {f"parkingSpot{self.spot_numbers[i]}": False}
                        self.mqtt_client.publish(Config.THINGSBOARD_PATH, telemetry, occupied_percentage)

        self.cap.release()

def main():
    mqtt_client = MQTTClient()
    detector = ParkingSpotDetector(mqtt_client)
    detector.run()
    mqtt_client.stop()

if __name__ == "__main__":
    main()
