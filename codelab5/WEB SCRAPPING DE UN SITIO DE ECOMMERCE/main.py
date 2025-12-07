# Importar librerías necesarias
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime

print("✅ Librerías importadas correctamente")

# Configuración del scraper
base_url = "http://books.toscrape.com"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def get_page_content(url):
    """Obtiene el contenido de una página"""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Error al acceder a {url}: {e}")
        return None

# Probar la conexión
print("🔄 Probando conexión...")
soup = get_page_content(base_url)
if soup:
    print("✅ Conexión exitosa")
    print(f"Título de la página: {soup.title.text}")
else:
    print("❌ Error en la conexión")

# Analizar la primera página
if soup:
    # Buscar productos
    products = soup.find_all('article', class_='product_pod')
    print(f"📚 Encontrados {len(products)} productos en la primera página")

    # Analizar el primer producto
    if products:
        first_product = products[0]
        print(f"\n🔍 Análisis del primer producto:")
        print(f"HTML del producto: {str(first_product)[:200]}...")

        # Buscar elementos específicos
        title_elem = first_product.find('h3')
        if title_elem:
            title_link = title_elem.find('a')
            if title_link:
                print(f"Título: {title_link.get('title', 'N/A')}")
                print(f"Enlace: {title_link.get('href', 'N/A')}")

        price_elem = first_product.find('p', class_='price_color')
        if price_elem:
            print(f"Precio: {price_elem.text}")

        rating_elem = first_product.find('p', class_='star-rating')
        if rating_elem:
            print(f"Rating: {rating_elem.get('class', 'N/A')}")

        availability_elem = first_product.find('p', class_='instock availability')
        if availability_elem:
            print(f"Disponibilidad: {availability_elem.text.strip()}")

    # Buscar enlace a la siguiente página
    next_link = soup.find('li', class_='next')
    if next_link:
        next_url = next_link.find('a')
        if next_url:
            print(f"\n➡️ Siguiente página: {next_url.get('href')}")
    else:
        print("\n❌ No se encontró enlace a la siguiente página")
else:
    print("❌ No se pudo analizar la página")

def extract_product_info(product_element):
    """Extrae información de un elemento de producto"""
    try:
        # Título del libro
        title_element = product_element.find('h3').find('a')
        title = title_element.get('title', '').strip()

        # URL del producto
        product_url = title_element.get('href', '')
        product_url = urljoin(base_url, product_url)

        # Precio
        price_element = product_element.find('p', class_='price_color')
        price = price_element.text.strip() if price_element else 'N/A'

        # Rating (estrellas)
        rating_element = product_element.find('p', class_='star-rating')
        rating = rating_element.get('class')[1] if rating_element else 'No rating'

        # Disponibilidad
        availability_element = product_element.find('p', class_='instock availability')
        availability = availability_element.text.strip() if availability_element else 'N/A'

        return {
            'title': title,
            'price': price,
            'rating': rating,
            'availability': availability,
            'product_url': product_url,
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"Error al extraer información del producto: {e}")
        return None

# Probar con el primer producto
if soup and products:
    print("🧪 Probando extracción del primer producto...")
    first_product_info = extract_product_info(products[0])
    if first_product_info:
        print("✅ Información extraída exitosamente:")
        for key, value in first_product_info.items():
            print(f"  {key}: {value}")
    else:
        print("❌ Error al extraer información")
else:
    print("❌ No hay productos para probar")

def scrape_all_books(max_pages=3):
    """Scraper completo que maneja múltiples páginas"""
    all_books = []
    current_page = 1

    print(f"🚀 Iniciando scraping de {max_pages} páginas...")

    while current_page <= max_pages:
        if current_page == 1:
            url = base_url
        else:
            url = f"{base_url}/catalogue/page-{current_page}.html"

        print(f"📄 Procesando página {current_page}...")

        soup = get_page_content(url)
        if not soup:
            print(f"❌ Error en página {current_page}")
            break

        # Verificar si hay productos en la página
        products = soup.find_all('article', class_='product_pod')
        if not products:
            print(f"❌ No se encontraron productos en página {current_page}")
            break

        # Extraer información de cada producto
        page_books = []
        for product in products:
            book_info = extract_product_info(product)
            if book_info:
                book_info['page'] = current_page
                page_books.append(book_info)

        all_books.extend(page_books)
        print(f"  ✅ Extraídos {len(page_books)} libros de la página {current_page}")

        # Pausa entre peticiones para ser respetuosos
        time.sleep(1)
        current_page += 1

    print(f"\n🎉 Scraping completado!")
    print(f"📊 Total de libros extraídos: {len(all_books)}")
    return all_books

# Ejecutar el scraper (limitado a 3 páginas para el ejemplo)
books = scrape_all_books(max_pages=3)

def clean_and_analyze_books(books_data):
    """Limpia y analiza los datos de libros"""
    if not books_data:
        print("❌ No hay datos para analizar")
        return None

    df = pd.DataFrame(books_data)

    print("=== INFORMACIÓN BÁSICA ===")
    print(f"Total de libros: {len(df)}")
    print(f"Columnas: {list(df.columns)}")

    # Limpiar precios
    def clean_price(price_str):
        if price_str == 'N/A':
            return 0.0
        # Extraer solo números del precio
        price_clean = re.sub(r'[^\d.]', '', price_str)
        try:
            return float(price_clean)
        except:
            return 0.0

    df['price_numeric'] = df['price'].apply(clean_price)

    # Análisis de precios
    print("\n=== ANÁLISIS DE PRECIOS ===")
    valid_prices = df[df['price_numeric'] > 0]
    if len(valid_prices) > 0:
        print(f"Precio promedio: £{valid_prices['price_numeric'].mean():.2f}")
        print(f"Precio mínimo: £{valid_prices['price_numeric'].min():.2f}")
        print(f"Precio máximo: £{valid_prices['price_numeric'].max():.2f}")

    # Análisis por rating
    print("\n=== ANÁLISIS POR RATING ===")
    rating_counts = df['rating'].value_counts()
    print(rating_counts)

    # Libros más caros
    if len(valid_prices) > 0:
        print("\n=== TOP 5 LIBROS MÁS CAROS ===")
        expensive_books = valid_prices.nlargest(5, 'price_numeric')[['title', 'price', 'rating']]
        for idx, row in expensive_books.iterrows():
            print(f"- {row['title']} - {row['price']} ({row['rating']})")

    return df

# Analizar los datos
if books:
    df_books = clean_and_analyze_books(books)
else:
    print("❌ No hay datos para analizar")

def search_books_by_criteria(df, criteria):
    """Busca libros por criterios específicos"""
    if df is None or df.empty:
        print("❌ No hay datos para buscar")
        return df

    results = df.copy()

    # Filtrar por título
    if 'title_keywords' in criteria:
        keywords = criteria['title_keywords'].lower().split()
        mask = results['title'].str.lower().str.contains('|'.join(keywords), na=False)
        results = results[mask]

    # Filtrar por precio
    if 'max_price' in criteria:
        results = results[results['price_numeric'] <= criteria['max_price']]

    if 'min_price' in criteria:
        results = results[results['price_numeric'] >= criteria['min_price']]

    # Filtrar por rating
    if 'min_rating' in criteria:
        rating_order = ['One', 'Two', 'Three', 'Four', 'Five']
        min_rating_idx = rating_order.index(criteria['min_rating'])
        valid_ratings = rating_order[min_rating_idx:]
        results = results[results['rating'].isin(valid_ratings)]

    return results

# Ejemplos de búsqueda
if 'df_books' in locals() and df_books is not None:
    print("=== BÚSQUEDAS ESPECÍFICAS ===")

    # Buscar libros sobre "python"
    python_books = search_books_by_criteria(df_books, {'title_keywords': 'python'})
    print(f"Libros sobre Python: {len(python_books)}")

    # Buscar libros baratos (menos de £10)
    cheap_books = search_books_by_criteria(df_books, {'max_price': 10})
    print(f"Libros baratos (<£10): {len(cheap_books)}")

    # Buscar libros con rating alto
    high_rated = search_books_by_criteria(df_books, {'min_rating': 'Four'})
    print(f"Libros con rating alto (4+ estrellas): {len(high_rated)}")

    # Mostrar algunos resultados
    if len(python_books) > 0:
        print(f"\n🐍 Libros sobre Python encontrados:")
        for idx, row in python_books.head(3).iterrows():
            print(f"- {row['title']} - {row['price']}")

    if len(cheap_books) > 0:
        print(f"\n💰 Libros baratos encontrados:")
        for idx, row in cheap_books.head(3).iterrows():
            print(f"- {row['title']} - {row['price']}")
else:
    print("❌ No hay datos para buscar")

def save_books_data(df, base_filename='books_data'):
    """Guarda los datos en diferentes formatos"""
    if df is None or df.empty:
        print("❌ No hay datos para guardar")
        return

    # CSV
    csv_filename = f"{base_filename}.csv"
    df.to_csv(csv_filename, index=False, encoding='utf-8')
    print(f"✅ Datos guardados en CSV: {csv_filename}")

    # Excel (si está disponible)
    try:
        excel_filename = f"{base_filename}.xlsx"
        df.to_excel(excel_filename, index=False)
        print(f"✅ Datos guardados en Excel: {excel_filename}")
    except ImportError:
        print("⚠️ Excel no disponible (instalar openpyxl para soporte)")

    # JSON
    json_filename = f"{base_filename}.json"
    df.to_json(json_filename, orient='records', indent=2)
    print(f"✅ Datos guardados en JSON: {json_filename}")

    # Resumen estadístico
    summary_filename = f"{base_filename}_summary.txt"
    with open(summary_filename, 'w', encoding='utf-8') as f:
        f.write("=== RESUMEN DE DATOS ===\n")
        f.write(f"Total de libros: {len(df)}\n")

        valid_prices = df[df['price_numeric'] > 0]
        if len(valid_prices) > 0:
            f.write(f"Precio promedio: £{valid_prices['price_numeric'].mean():.2f}\n")
            f.write(f"Precio mínimo: £{valid_prices['price_numeric'].min():.2f}\n")
            f.write(f"Precio máximo: £{valid_prices['price_numeric'].max():.2f}\n")

        f.write(f"\nDistribución por rating:\n")
        f.write(df['rating'].value_counts().to_string())

    print(f"✅ Resumen guardado en: {summary_filename}")

# Guardar todos los datos
if 'df_books' in locals() and df_books is not None:
    save_books_data(df_books)
else:
    print("❌ No hay datos para guardar")