import re, random, numpy as np, pandas as pd  # re=expresiones regulares; random/numpy/pandas=datos y utilidades
from sklearn.model_selection import train_test_split, cross_val_score  # dividir datos y validar (cross-validation)
from sklearn.pipeline import make_pipeline  # encadenar pasos (vectorizador + modelo) en un solo objeto
from sklearn.feature_extraction.text import TfidfVectorizer  # convierte texto a números (TF-IDF)
from sklearn.linear_model import LogisticRegression  # clasificador lineal que devuelve probabilidades
from sklearn.metrics import (classification_report, confusion_matrix,
                             accuracy_score, precision_recall_curve,
                             average_precision_score)  # métricas para evaluar y calibrar umbrales
import matplotlib.pyplot as plt  # para graficar curva precisión-recall
import joblib  # guardar/cargar el pipeline entrenado

random.seed(42); np.random.seed(42)  # fijamos semillas: resultados reproducibles al repetir el script

# 1) Dataset sintético realista (puedes reemplazar por tu CSV real)
#   - Objetivo: distinguir spam/estafa (1) de mensajes legítimos (0).
#   - En un caso real leerías desde CSV/BD con columnas como id, texto, etiqueta.
#   - Aquí simulamos ejemplos cortos y variados.
#   - 1 = spam/estafa, 0 = legítimo
spam = [
    "Gana dinero fácil en 24 horas, haz clic aquí",
    "Has sido seleccionado para un premio, comparte tus datos",
    "Tu cuenta será cerrada, verifica en este enlace",
    "Crypto inversión garantizada 10% diario",
    "Último aviso: paga ahora para evitar bloqueo de cuenta",
    "Te transfiero 1000 USD si completas este formulario",
    "Promoción exclusiva solo hoy, ingresa tu tarjeta",
    "Recarga gratis, solo confirma tu contraseña",
    "WhatsApp Premium sin costo, descarga aquí",
    "Factura vencida, ingresa a este link para pagar"
]
legit = [
    "Hola, necesito soporte para iniciar sesión",
    "¿Cuánto cuesta el plan anual y medios de pago?",
    "El pedido llegó tarde, ¿pueden ayudarme?",
    "Estoy interesado en una demo del producto",
    "¿Tienen descuento por volumen para empresas?",
    "Se cierra la app al abrir el carrito, por favor apoyo",
    "El envío llegó bien, gracias por la atención",
    "Deseo actualizar mi método de pago",
    "¿Cuál es el tiempo de entrega estimado?",
    "Quiero cambiar la contraseña de mi cuenta"
]

def variar(s):
    # Aumentación simple de datos: añade pequeñas coletillas para crear variantes del mismo patrón.
    # Esto ayuda al modelo a generalizar ante cambios menores en el texto.
    extras = ["", "!", "!!", " urgente", " por favor", " ahora", " hoy", " gratis"]
    return s + random.choice(extras)

data = []
for _ in range(25):  # repetimos para aumentar el dataset con variantes leves
    data += [(variar(x), 1) for x in spam]
    data += [(variar(x), 0) for x in legit]

# Creamos un DataFrame con columnas: texto (entrada) y etiqueta (objetivo)
# sample(frac=1) mezcla filas; reset_index deja el índice ordenado tras mezclar
df = pd.DataFrame(data, columns=["texto","etiqueta"]).sample(frac=1, random_state=42).reset_index(drop=True)
print("Muestras:", len(df), " | Spam:", int(df['etiqueta'].sum()), " | Legítimos:", int((1-df['etiqueta']).sum()))

# 2) Limpieza simple
#    Normalizamos el texto: minúsculas, quitamos signos raros, compactamos espacios.
#    Nota: conservamos acentos y "ñ" porque son útiles en español.
def limpiar(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-záéíóúñü0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

df["texto_clean"] = df["texto"].apply(limpiar)

# 3) Split estratificado
#    Separamos en entrenamiento (80%) y prueba (20%).
#    stratify conserva la proporción de spam/legítimos en ambos conjuntos.
X_train, X_test, y_train, y_test = train_test_split(
    df["texto_clean"], df["etiqueta"], test_size=0.2, random_state=42, stratify=df["etiqueta"]
)

# 4) Pipeline TF-IDF + Regresión Logística (con balance por si hay leves desbalances)
#    TfidfVectorizer: convierte texto a una matriz numérica (unigrams+bigrams; ignora términos raros)
#    LogisticRegression: modelo lineal que devuelve probabilidades para ajustar umbrales luego.
#    class_weight="balanced": compensa si hay más ejemplos de una clase que de otra.
pipe = make_pipeline(
    TfidfVectorizer(max_features=30000, ngram_range=(1,2), min_df=2),
    LogisticRegression(max_iter=200, class_weight="balanced", n_jobs=-1, solver="liblinear")
)

# 5) Entrenar y evaluar (umbral por defecto 0.5)
#    fit entrena el pipeline completo; predict usa umbral 0.5 por defecto para decidir 0/1.
pipe.fit(X_train, y_train)
pred = pipe.predict(X_test)
acc = accuracy_score(y_test, pred)
print(f"\nAccuracy test (umbral 0.5): {acc:.3f}\n")
print("Reporte por clase:\n", classification_report(y_test, pred, digits=3))  # precision/recall/F1 por clase

cm = confusion_matrix(y_test, pred, labels=[0,1])
print("\nMatriz de confusión (filas=real, cols=pred):\n",
      pd.DataFrame(cm, index=["real_legit(0)","real_spam(1)"], columns=["pred_legit(0)","pred_spam(1)"]))

# 6) Ajuste de umbral según tu prioridad (menos falsos positivos o menos falsos negativos)
#   Obtenemos probabilidades de spam (clase 1) para decidir el umbral manualmente.
probs = pipe.predict_proba(X_test)[:, 1]
ap = average_precision_score(y_test, probs)
precision, recall, thresholds = precision_recall_curve(y_test, probs)
print(f"\nAverage Precision (área precisión-recall): {ap:.3f}")

#   Elegimos un umbral que priorice, por ejemplo, ALTA PRECISIÓN al marcar spam
#   (reduce falsos positivos: evitar etiquetar legítimos como spam).
def evaluar_umbral(t):
    p = (probs >= t).astype(int)
    return accuracy_score(y_test, p)

umbral = 0.7  # puedes moverlo: ~0.3 (recall alto) ... ~0.7 (precision alta)
pred_u = (probs >= umbral).astype(int)
print(f"\nAccuracy con umbral {umbral}: {accuracy_score(y_test, pred_u):.3f}")
print("Reporte por clase con umbral ajustado:\n", classification_report(y_test, pred_u, digits=3))
print("Matriz con umbral ajustado:\n",
      pd.DataFrame(confusion_matrix(y_test, pred_u, labels=[0,1]),
                   index=["real_legit(0)","real_spam(1)"], columns=["pred_legit(0)","pred_spam(1)"]))

#   (Opcional) Curva Precisión-Recall para decidir el umbral visualmente
plt.figure()
plt.step(recall, precision, where="post")
plt.xlabel("Recall (sensibilidad para spam)")
plt.ylabel("Precision (acierto cuando digo spam)")
plt.title("Curva Precisión–Recall (elige umbral según tu prioridad)")
plt.show()

# 7) Validación cruzada (estable)
#    cross_val_score re-entrena y evalúa con diferentes particiones (k=5) para estimar estabilidad.
scores = cross_val_score(pipe, df["texto_clean"], df["etiqueta"], cv=5, scoring="f1_macro")
print(f"\nCV 5-fold F1_macro: media={scores.mean():.3f} ±{scores.std():.3f}")

# 8) Uso en vida real: clasificar mensajes nuevos con umbral ajustado
#    Recibe textos, calcula probabilidad de spam y aplica el umbral elegido.
#    Devuelve una lista con (texto_original, prob_spam_redondeada, etiqueta_amigable).
def clasificar_mensajes(textos, threshold=0.7):
    tx = [limpiar(t) for t in textos]
    prob = pipe.predict_proba(tx)[:, 1]
    yhat = (prob >= threshold).astype(int)
    etiqueta = ["spam/estafa" if i==1 else "legítimo" for i in yhat]
    return list(zip(textos, prob.round(3), etiqueta))

nuevos = [
    "Has sido seleccionado para un premio, comparte tus datos aquí",
    "Necesito recuperar acceso a mi cuenta, me pueden ayudar?",
    "Gana dinero rápido hoy, sin riesgo, solo ingresa tu tarjeta",
    "Hola, ¿cuál es el precio del plan anual y si aceptan tarjeta?"
]
print("\nMensajes nuevos clasificados (umbral 0.7):")
for t, p, e in clasificar_mensajes(nuevos, threshold=0.7):
    print(f"- '{t}' -> prob_spam={p} | clase={e}")

# 9) Guardar y cargar un ÚNICO pipeline (producción)
#    Guardamos el pipeline completo (vectorizador + modelo) para reutilizar sin reentrenar.
joblib.dump(pipe, "pipeline_spam.joblib")
print("\nPipeline guardado en pipeline_spam.joblib")

# Carga y uso posterior:
#    Ejemplo de cómo cargar y predecir directamente sobre un texto nuevo.
loaded = joblib.load("pipeline_spam.joblib")
print("Test carga:", loaded.predict(["Gana dinero fácil completando este formulario"])[0])  # 1=spam, 0=legítimo