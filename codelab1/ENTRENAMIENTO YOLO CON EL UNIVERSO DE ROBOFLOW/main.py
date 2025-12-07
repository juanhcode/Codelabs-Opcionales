import os
from roboflow import Roboflow
from ultralytics import YOLO

# Cargar dataset desde Roboflow
rf = Roboflow(api_key=os.environ["ROBOFLOW_API_KEY"])
project = rf.workspace("roboflow-universe-projects").project("license-plate-recognition-rxg4e")
dataset = project.version(1).download("yolov8")  # Cambia el número si hay una versión más nueva

# Cargar modelo entrenado (usa la ruta donde quedó tu mejor modelo)
model = YOLO("runs/detect/train2/weights/best.pt")

# Predecir sobre una imagen local
results = model("placa.jpeg")

# Mostrar resultados
results.show()
