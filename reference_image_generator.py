import cv2
import time

# Inicializa la cámara
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("No se puede abrir la cámara")
    exit()

# Esperar 3 segundos para que la cámara esté lista
print("Iniciando cámara...")
time.sleep(3)

# Capturar una imagen
ret, frame = cap.read()
if not ret:
    print("Error al capturar el frame")
    cap.release()
    exit()

# Dimensiones de la imagen
height, width, _ = frame.shape

# Configuración de texto y líneas
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.25  # Tamaño del texto
color = (0, 0, 0)
thickness = 1
line_thickness = 1

# Intervalos de las marcas (cada 20 píxeles)
interval = 20

# Dibujar las referencias horizontales (superior e inferior)
for x in range(0, width, interval):
    # Dibujar líneas horizontales superiores e inferiores
    cv2.line(frame, (x, 0), (x, 10), color, line_thickness)  # Superior
    cv2.line(frame, (x, height - 10), (x, height), color, line_thickness)  # Inferior
    # Agregar texto de referencia
    cv2.putText(frame, str(x), (x, 25), font, font_scale, color, thickness)  # Superior
    cv2.putText(frame, str(x), (x, height - 15), font, font_scale, color, thickness)  # Inferior

# Dibujar las referencias verticales (izquierda y derecha)
for y in range(0, height, interval):
    # Dibujar líneas verticales izquierda y derecha
    cv2.line(frame, (0, y), (10, y), color, line_thickness)  # Izquierda
    cv2.line(frame, (width - 10, y), (width, y), color, line_thickness)  # Derecha
    # Agregar texto de referencia
    cv2.putText(frame, str(y), (15, y + 5), font, font_scale, color, thickness)  # Izquierda
    cv2.putText(frame, str(y), (width - 40, y + 5), font, font_scale, color, thickness)  # Derecha

# Guardar la imagen con las referencias en un archivo
output_path = "output_image_with_references.jpg"  # Ruta donde se guardará la imagen
cv2.imwrite(output_path, frame)
print(f"Imagen guardada en: {output_path}")

# Liberar la cámara
cap.release()
