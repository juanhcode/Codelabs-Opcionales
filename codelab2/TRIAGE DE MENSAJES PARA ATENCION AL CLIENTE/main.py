import re, random, numpy as np, pandas as pd  # re=expresiones regulares, random=aleatoriedad, numpy/pandas=manipulación de datos
from sklearn.model_selection import train_test_split, cross_val_score  # utilidades para dividir datos y validar
from sklearn.pipeline import make_pipeline  # encadena pasos de preprocesamiento + modelo en un solo objeto
from sklearn.feature_extraction.text import TfidfVectorizer  # convierte texto en vectores numéricos (TF-IDF)
from sklearn.svm import LinearSVC  # clasificador SVM lineal (rápido y efectivo para texto)
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score  # métricas para evaluar el modelo
import joblib  # guardar y cargar modelos entrenados (a disco)

random.seed(42); np.random.seed(42)  # fijamos semillas para que los resultados sean reproducibles

# 1) Dataset sintético realista (puedes reemplazar por tu CSV real)
#    Objetivo: tener ejemplos de 3 categorías típicas de atención: ventas, soporte, queja.
#    En un proyecto real, leerías un CSV/BD con columnas como id, texto, etiqueta.
ventas = [
    "Quiero saber el precio del plan premium",
    "¿Tienen descuentos por volumen para empresas?",
    "¿Cómo puedo pagar? ¿Tarjeta o transferencia?",
    "Estoy interesado en comprar 10 unidades",
    "¿Cuánto cuesta el plan anual y cómo se factura?"
]
soporte = [
    "No puedo iniciar sesión, sale error 403",
    "La app se cierra al abrir el carrito",
    "La impresora no conecta por wifi, ya reinicié",
    "Se perdió mi pedido en la app, ayuda",
    "No me llega el código de verificación"
]
queja = [
    "El pedido llegó incompleto y nadie responde",
    "Muy mala atención, llegó tarde y mal empacado",
    "Estoy inconforme, el producto vino dañado",
    "Demasiada demora, pésimo servicio",
    "Me trataron mal por WhatsApp, muy groseros"
]

def variar(s):
    # Pequeña "aumentación" de datos: agregamos palabras comunes al final para crear variantes.
    # Esto ayuda a que el modelo vea ligeras diferencias y generalice mejor.
    extras = ["", "!", "!!", " por favor", " urgente", " de verdad", " gracias"]
    return s + random.choice(extras)

data = []
for _ in range(20):  # repetimos 20 veces para generar más datos con pequeñas variaciones
    data += [(variar(x), "ventas") for x in ventas]
    data += [(variar(x), "soporte") for x in soporte]
    data += [(variar(x), "queja")   for x in queja]

# Creamos un DataFrame con dos columnas: texto (entrada) y etiqueta (clase objetivo)
# sample(frac=1) mezcla las filas; reset_index solo limpia los índices tras mezclar
df = pd.DataFrame(data, columns=["texto","etiqueta"]).sample(frac=1, random_state=42).reset_index(drop=True)
print("Muestras:", len(df), df["etiqueta"].value_counts().to_dict())

# 2) Limpieza simple
#    Normalizamos el texto: minúsculas, quitamos signos raros, compactamos espacios.
#    Nota: mantener tildes y "ñ" puede ser útil para español.

def limpiar(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-záéíóúñü0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

df["texto_clean"] = df["texto"].apply(limpiar)

# 3) Split estratificado
#    Separamos datos en entrenamiento (80%) y prueba (20%).
#    stratify mantiene la proporción de clases en ambos conjuntos.
X_train, X_test, y_train, y_test = train_test_split(
    df["texto_clean"], df["etiqueta"], test_size=0.2, random_state=42, stratify=df["etiqueta"]
)

# 4) Pipeline TF-IDF + SVM (class_weight='balanced' por si hay leves desbalances)
#    El Pipeline encadena: TfidfVectorizer (convierte texto a números) -> LinearSVC (clasificador).
#    ngram_range=(1,2) usa palabras sueltas y pares de palabras; min_df=2 ignora términos rarísimos.
#    class_weight="balanced" ayuda si una clase aparece menos que otras.
pipe = make_pipeline(
    TfidfVectorizer(max_features=30000, ngram_range=(1,2), min_df=2),
    LinearSVC(class_weight="balanced", random_state=42)
)

# 5) Entrenamiento y evaluación
#    fit entrena el pipeline; predict obtiene la clase para cada texto de prueba.
pipe.fit(X_train, y_train)
pred = pipe.predict(X_test)

acc = accuracy_score(y_test, pred)  # accuracy = proporción de aciertos totales
print(f"\nAccuracy test: {acc:.3f}\n")
print("Reporte por clase:\n", classification_report(y_test, pred, digits=3))  # precision, recall, f1 por clase
cm = confusion_matrix(y_test, pred, labels=["ventas","soporte","queja"])
print("\nMatriz de confusión (filas=real, cols=pred):\n", pd.DataFrame(cm,
      index=["real_ventas","real_soporte","real_queja"],
      columns=["pred_ventas","pred_soporte","pred_queja"]))

# 6) Validación cruzada (usa SU PROPIO vectorizador dentro del pipeline)
#    cross_val_score rehace el pipeline varias veces (k=5) con particiones distintas.
#    f1_macro promedia el F1 de cada clase, útil si las clases no están perfectamente balanceadas.
scores = cross_val_score(pipe, df["texto_clean"], df["etiqueta"], cv=5, scoring="f1_macro")
print(f"\nCV 5-fold F1_macro: media={scores.mean():.3f} ±{scores.std():.3f}")

# 7) Enrutador de mensajes (utilidad directa)
#    Recibe una lista de textos, limpia cada uno, predice su clase
#    y devuelve tuplas (texto_original, etiqueta_predicha, area_destino)
def enrutar_mensajes(textos):
    tx = [limpiar(t) for t in textos]
    etiquetas = pipe.predict(tx)
    # mapa a área/equipo real (puedes cambiar nombres)
    area = {"ventas":"Equipo Ventas", "soporte":"Mesa Soporte", "queja":"Atención al Cliente"}
    rutas = [area[e] for e in etiquetas]
    return list(zip(textos, etiquetas, rutas))

nuevos = [
    "Se dañó el botón de encendido, necesito ayuda urgentemente",
    "¿Hacen descuento si compro 15 licencias?",
    "Estoy muy molesto: llegó tarde y la caja rota, pésimo servicio"
]
print("\nEnrutamiento de mensajes nuevos:")
for texto, etiqueta, ruta in enrutar_mensajes(nuevos):
    print(f"- '{texto}' -> clase: {etiqueta} | ruta: {ruta}")

# 8) Guardar y cargar (producción) — un único .joblib
#    Guardamos TODO el pipeline (limpieza + vectorizador + clasificador) en un solo archivo.
#    Así, al cargarlo luego, podemos predecir directamente sin reentrenar ni reconfigurar.
joblib.dump(pipe, "pipeline_triage.joblib")
print("\nPipeline guardado en pipeline_triage.joblib")

# Uso posterior:
#    Ejemplo de cómo cargar el pipeline guardado y usarlo para predecir un mensaje nuevo.
loaded = joblib.load("pipeline_triage.joblib")
print("Test carga:", loaded.predict(["No puedo entrar a mi cuenta, sale error 500"])[0])

# 9) (Opcional) Clasificación en lote desde CSV real
#    Si tienes un archivo real con mensajes, puedes clasificar en lote y exportar resultados.
# df_real = pd.read_csv("mensajes.csv")  # columnas: id, texto
# df_real["texto_clean"] = df_real["texto"].apply(limpiar)
# df_real["etiqueta"] = loaded.predict(df_real["texto_clean"])
# df_real["ruta"] = df_real["etiqueta"].map({"ventas":"Equipo Ventas","soporte":"Mesa Soporte","queja":"Atención al Cliente"})
# df_real.to_csv("mensajes_enrutados.csv", index=False)
# print("Archivo 'mensajes_enrutados.csv' generado con la ruta de cada mensaje.")