import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import yfinance as yf
import re
import urllib.parse

class NewsModule:
    def __init__(self):
        self.positive_words = ['surge', 'rise', 'gain', 'record', 'dividend', 'bonus', 'acquisition', 'profit', 'growth', 'up']
        self.negative_words = ['fall', 'drop', 'penalty', 'fraud', 'default', 'investigation', 'loss', 'down', 'decline', 'crash']

    def keyword_sentiment(self, text):
        text = text.lower()
        score = 0
        matches = 0
        
        for w in self.positive_words:
            if re.search(r'\b' + w + r'\b', text):
                score += 1
                matches += 1
                
        for w in self.negative_words:
            if re.search(r'\b' + w + r'\b', text):
                score -= 1
                matches += 1
                
        if matches == 0:
            return 0
            
        normalized = max(min(score / matches, 1.0), -1.0)
        return normalized

    def fetch_google_news(self, query):
        encoded_query = urllib.parse.quote(f"{query} stock")
        url = f"https://news.google.com/rss/search?q={encoded_query}"
        
        articles = []
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall('.//item'):
                    title = item.find('title').text
                    link = item.find('link').text
                    pub_date = item.find('pubDate').text
                    source = item.find('source').text if item.find('source') is not None else "Google News"
                    
                    if len(title) < 15 or 'newsletter' in title.lower() or 'privacy policy' in title.lower():
                        continue
                        
                    sentiment_score = self.keyword_sentiment(title)
                    
                    if sentiment_score >= 0.15:
                        label = "Positive"
                        emoji = "📈"
                    elif sentiment_score <= -0.15:
                        label = "Negative"
                        emoji = "📉"
                    else:
                        label = "Neutral"
                        emoji = "➖"
                        
                    articles.append({
                        "title": title,
                        "link": link,
                        "date": pub_date,
                        "source": source,
                        "sentiment": sentiment_score,
                        "label": label,
                        "emoji": emoji
                    })
                    
                    if len(articles) >= 15:
                        break
        except Exception as e:
            print(f"Error fetching Google News: {e}")
            
        return articles

    def fetch_yfinance_news(self, symbol):
        articles = []
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            for item in news:
                title = item.get('title', '')
                link = item.get('link', '')
                pub_time = item.get('providerPublishTime', 0)
                source = item.get('publisher', 'Yahoo Finance')
                
                if len(title) < 15: continue
                
                date = datetime.fromtimestamp(pub_time).strftime('%a, %d %b %Y %H:%M:%S GMT')
                sentiment_score = self.keyword_sentiment(title)
                
                if sentiment_score >= 0.15:
                    label = "Positive"
                    emoji = "📈"
                elif sentiment_score <= -0.15:
                    label = "Negative"
                    emoji = "📉"
                else:
                    label = "Neutral"
                    emoji = "➖"
                    
                articles.append({
                    "title": title,
                    "link": link,
                    "date": date,
                    "source": source,
                    "sentiment": sentiment_score,
                    "label": label,
                    "emoji": emoji
                })
                
                if len(articles) >= 15:
                    break
        except Exception as e:
            print(f"Error fetching YFinance news: {e}")
            
        return articles

    def get_news(self, company_name, symbol=None):
        query = company_name if company_name else symbol
        if not query:
            return []
            
        articles = self.fetch_google_news(query)
        
        if len(articles) < 5 and symbol:
            yf_articles = self.fetch_yfinance_news(symbol)
            
            existing_links = {a['link'] for a in articles}
            for yfa in yf_articles:
                if yfa['link'] not in existing_links:
                    articles.append(yfa)
                    
        return articles[:15]
