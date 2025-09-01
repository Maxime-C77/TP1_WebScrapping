import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pymongo import MongoClient


def fetch_article(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        article_data = {}

        title_tag = soup.find('h1', class_="entry-title")
        article_data['title'] = title_tag.get_text(strip=True) if title_tag else None

        thumbnail_tag = soup.find('figure', class_='article-hat-img')
        if thumbnail_tag and thumbnail_tag.find('img'):
            article_data['thumbnail'] = extract_img_url(thumbnail_tag.find('img'))
        else:
            article_data['thumbnail'] = None

        summary_list = []
        toc = soup.find('ol', class_="summary-inner")
        if toc:
            for li in toc.find_all('li'):
                summary_list.append(li.get_text(strip=True))
        article_data['summary'] = summary_list

        category_tag = soup.find('h2', class_='post-190096-titre^')
        article_data['subcategory'] = category_tag.get_text(strip=True) if category_tag else None

        excerpt_tag = soup.find('div', class_="article-hat")
        article_data['excerpt'] = excerpt_tag.get_text(strip=True) if excerpt_tag else None

        date_tag = soup.find('time', class_='entry-date')
        if date_tag and date_tag.has_attr("datetime"):
            raw_date = date_tag['datetime']
            try:
                article_data['date'] = datetime.fromisoformat(raw_date).strftime("%Y-%m-%d")
            except Exception:
                article_data['date'] = raw_date
        else:
            article_data['date'] = None

        author_tag = soup.find('span', class_="byline")
        article_data['author'] = author_tag.get_text(strip=True) if author_tag else None

        content_div = soup.find('div', class_="entry-content")
        if content_div:
            paragraphs = [p.get_text(" ", strip=True) for p in content_div.find_all(['p', 'h2', 'h3', 'h4'])]
            article_data['content'] = "\n\n".join(paragraphs)
        else:
            article_data['content'] = None

        alt_tag = soup.find('figcaption' , class_="legend")
        images_data = []
        if content_div:
            for img in content_div.find_all('img'):
                img_info = {
                    "url": extract_img_url(img),
                    "alt": img.get('alt_tag', None),
                }
                images_data.append(img_info)
        article_data['images'] = images_data

        

        save_to_mongo(article_data)

        return article_data

    except requests.exceptions.RequestException as e:
        print(f"Erreur de requête : {e}")
        return None


def extract_img_url(img_tag):
    """Extrait l'URL d'une image depuis plusieurs attributs possibles."""
    if not img_tag:
        return None
    url_attrs = ['src', 'data-lazy-src', 'data-lazy-srcset']
    for attr in url_attrs:
        if img_tag.has_attr(attr):
            url = img_tag[attr]
            if url and url.startswith('http'):
                return url
    return None


def save_to_mongo(article_data):
    """Connexion et insertion dans MongoDB"""
    client = MongoClient("mongodb+srv://mcordier:BHk9Zz8k9DsxHR3Q@cluster0.8uuayyf.mongodb.net/") 
    db = client['scraping_db']
    collection = db['article']
    collection.insert_one(article_data)
    print("Article sauvegardé dans MongoDB.")


if __name__ == "__main__":
    url = "https://www.blogdumoderateur.com/selection-formation-chef-projet-web-267"
    data = fetch_article(url)
    if data:
        print(data)
