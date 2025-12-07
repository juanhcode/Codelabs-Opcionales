# Importar librerías
import requests
from bs4 import BeautifulSoup
import pandas as pd
import csv
import time
from datetime import datetime
import re

print("✅ Librerías importadas correctamente")

# URL del sitio de noticias
url = "https://news.ycombinator.com"

# Headers para simular un navegador real
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# AJAX: ASYNCHROUS JAVASCRIPT AND XML (xhr = XmlHttpRequest())
# //*[@id="45372286"]/td[1]
# [id="\34 5372286"] > td:nth-child(1)

# Hacer la petición
response = requests.get(url, headers=headers)
print(f"Status Code: {response.status_code}")
print(f"Content Length: {len(response.text)}")

# Verificar que la petición fue exitosa
if response.status_code == 200:
    print("✅ Petición exitosa")
else:
    print("❌ Error en la petición")

# Parsear el HTML
soup = BeautifulSoup(response.text, 'html.parser')

# Primero, vamos a explorar la estructura del HTML
print("🔍 Explorando la estructura del HTML...")

# Buscar diferentes tipos de enlaces
story_links = soup.find_all('a', class_='titlelink')
story_links_alt = soup.find_all('a', class_='storylink')
all_links = soup.find_all('a')

print(f"Enlaces con clase 'titlelink': {len(story_links)}")
print(f"Enlaces con clase 'storylink': {len(story_links_alt)}")
print(f"Total de enlaces: {len(all_links)}")

# Buscar enlaces que contengan noticias (más flexible)
news_links = []
for link in all_links:
    href = link.get('href', '')
    text = link.text.strip()

    # Filtrar enlaces que parecen ser noticias
    if (href and text and
        not href.startswith('#') and
        not href.startswith('javascript:') and
        len(text) > 10 and
        'item?id=' not in href):
        news_links.append(link)

print(f"Enlaces potenciales de noticias: {len(news_links)}")

# Mostrar los primeros enlaces encontrados
if news_links:
    print(f"\n📰 Primeros 3 enlaces encontrados:")
    for i, link in enumerate(news_links[:3], 1):
        print(f"{i}. {link.text[:50]}...")
        print(f"   URL: {link.get('href')}")
        print()
else:
    print("❌ No se encontraron enlaces de noticias")

    # Vamos a ver qué clases existen
    print("\n🔍 Clases de enlaces disponibles:")
    link_classes = set()
    for link in all_links[:20]:  # Solo los primeros 20
        class_name = link.get('class')
        if class_name:
            link_classes.add(' '.join(class_name))

    for cls in sorted(link_classes):
        print(f"  - {cls}")

def scrape_hn_news():
    """Extrae noticias de Hacker News con estrategia robusta"""
    url = "https://news.ycombinator.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = []

        # Estrategia 1: Buscar por filas de noticias
        rows = soup.find_all('tr', class_='athing')
        print(f"Encontradas {len(rows)} filas de noticias")

        if not rows:
            # Estrategia 2: Buscar enlaces de noticias directamente
            print("🔄 Intentando estrategia alternativa...")
            all_links = soup.find_all('a')

            for link in all_links:
                href = link.get('href', '')
                text = link.text.strip()

                # Filtrar enlaces que parecen ser noticias
                if (href and text and
                    len(text) > 10 and
                    not href.startswith('#') and
                    not href.startswith('javascript:') and
                    'item?id=' not in href and
                    'user?id=' not in href and
                    'show' not in href):

                    # Hacer enlace absoluto si es relativo
                    if href.startswith('/'):
                        href = 'https://news.ycombinator.com' + href
                    elif not href.startswith('http'):
                        href = 'https://news.ycombinator.com/' + href

                    news_items.append({
                        'title': text,
                        'link': href,
                        'score': 'N/A',
                        'comments': 'N/A',
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })

            # Limitar a las primeras 20 noticias
            news_items = news_items[:20]
        else:
            # Estrategia original con filas
            for row in rows:
                # Buscar enlaces de título
                title_links = row.find_all('a')
                for title_link in title_links:
                    href = title_link.get('href', '')
                    text = title_link.text.strip()

                    if text and len(text) > 5:
                        # Hacer enlace absoluto si es relativo
                        if href.startswith('/'):
                            href = 'https://news.ycombinator.com' + href
                        elif not href.startswith('http'):
                            href = 'https://news.ycombinator.com/' + href

                        # Buscar score y comentarios
                        score = 'N/A'
                        comments = 'N/A'

                        try:
                            next_row = row.find_next_sibling('tr')
                            if next_row:
                                score_span = next_row.find('span', class_='score')
                                if score_span:
                                    score = score_span.text

                                comments_link = next_row.find('a', href=lambda x: x and 'item?id=' in x)
                                if comments_link:
                                    comments = comments_link.text
                        except:
                            pass

                        news_items.append({
                            'title': text,
                            'link': href,
                            'score': score,
                            'comments': comments,
                            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        break  # Solo tomar el primer enlace de cada fila

        return news_items

    except requests.RequestException as e:
        print(f"Error al hacer la petición: {e}")
        return []

# Ejecutar la función
print("🔄 Extrayendo noticias...")
news = scrape_hn_news()
print(f"✅ Extraídas {len(news)} noticias")

# Mostrar las primeras 5 noticias
if news:
    print("\n📰 Primeras 5 noticias:")
    for i, item in enumerate(news[:5], 1):
        print(f"{i}. {item['title']}")
        print(f"   Enlace: {item['link']}")
        print(f"   Puntos: {item['score']}")
        print(f"   Comentarios: {item['comments']}")
        print()
else:
    print("❌ No se pudieron extraer noticias")

def save_to_csv(news_data, filename='hacker_news.csv'):
    """Guarda los datos en un archivo CSV"""
    if not news_data:
        print("❌ No hay datos para guardar")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Título', 'Enlace', 'Puntos', 'Comentarios', 'Fecha'])

        for item in news_data:
            writer.writerow([
                item['title'],
                item['link'],
                item['score'],
                item['comments'],
                item['scraped_at']
            ])

    print(f"✅ Datos guardados en {filename}")

# Guardar los datos
if news:
    save_to_csv(news)
else:
    print("❌ No hay datos para guardar")

def analyze_news_data(news_data):
    """Analiza los datos extraídos"""
    if not news_data:
        print("❌ No hay datos para analizar")
        return

    print("=== ANÁLISIS DE DATOS ===")
    print(f"Total de noticias: {len(news_data)}")

    # Crear DataFrame para análisis
    df = pd.DataFrame(news_data)

    # Análisis de títulos
    print(f"\n📊 Estadísticas de títulos:")
    print(f"Título más largo: {df['title'].str.len().max()} caracteres")
    print(f"Título más corto: {df['title'].str.len().min()} caracteres")
    print(f"Longitud promedio: {df['title'].str.len().mean():.1f} caracteres")

    # Análisis de enlaces
    print(f"\n🔗 Análisis de enlaces:")
    external_links = df[~df['link'].str.contains('news.ycombinator.com', na=False)]
    print(f"Enlaces externos: {len(external_links)}")
    print(f"Enlaces internos: {len(df) - len(external_links)}")

    # Análisis de scores (si están disponibles)
    scores_available = df[df['score'] != 'N/A']
    if len(scores_available) > 0:
        print(f"\n⭐ Análisis de puntuaciones:")
        print(f"Noticias con puntuación: {len(scores_available)}")

        # Extraer números de los scores
        score_numbers = []
        for score in scores_available['score']:
            numbers = re.findall(r'\d+', score)
            if numbers:
                score_numbers.append(int(numbers[0]))

        if score_numbers:
            print(f"Puntuación máxima: {max(score_numbers)}")
            print(f"Puntuación mínima: {min(score_numbers)}")
            print(f"Puntuación promedio: {sum(score_numbers)/len(score_numbers):.1f}")

    return df

# Ejecutar análisis
if news:
    df_news = analyze_news_data(news)
else:
    print("❌ No hay datos para analizar")

def filter_news_by_keyword(news_data, keywords):
    """Filtra noticias por palabras clave"""
    if not news_data:
        return []

    filtered = []
    keywords_lower = [kw.lower() for kw in keywords]

    for item in news_data:
        title_lower = item['title'].lower()
        if any(keyword in title_lower for keyword in keywords_lower):
            filtered.append(item)

    return filtered

def filter_news_by_score(news_data, min_score=0):
    """Filtra noticias por puntuación mínima"""
    if not news_data:
        return []

    filtered = []
    for item in news_data:
        score_text = item['score']
        if score_text != 'N/A':
            numbers = re.findall(r'\d+', score_text)
            if numbers and int(numbers[0]) >= min_score:
                filtered.append(item)

    return filtered

# Ejemplos de filtrado
if news:
    print("🔍 EJEMPLOS DE FILTRADO")
    print("=" * 30)

    # Filtrar por palabras clave
    python_news = filter_news_by_keyword(news, ['python', 'programming', 'code'])
    print(f"Noticias sobre programación: {len(python_news)}")

    ai_news = filter_news_by_keyword(news, ['AI', 'artificial intelligence', 'machine learning'])
    print(f"Noticias sobre IA: {len(ai_news)}")

    # Mostrar noticias filtradas
    if python_news:
        print(f"\n🐍 Noticias sobre programación:")
        for i, item in enumerate(python_news[:3], 1):
            print(f"{i}. {item['title']}")

    if ai_news:
        print(f"\n🤖 Noticias sobre IA:")
        for i, item in enumerate(ai_news[:3], 1):
            print(f"{i}. {item['title']}")
else:
    print("❌ No hay datos para filtrar")