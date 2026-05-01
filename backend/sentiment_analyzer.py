import re
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

class SentimentAnalyzer:
    def __init__(self):
        # Keyword-based analyzer setup
        self.event_weights = {
            'special dividend': 0.70, 'bonus issue': 0.70, 'stock split': 0.60,
            'profit increase': 0.65, 'revenue growth': 0.60, 'acquisition': 0.50,
            'fraud': -0.80, 'insolvency': -0.80, 'bankruptcy': -0.80, 'default': -0.75,
            'penalty': -0.60, 'loss': -0.50, 'resignation': -0.40, 'lawsuit': -0.50
        }
        
        # HuggingFace FinBERT
        try:
            self.finbert = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        except Exception:
            self.finbert = None
            
        # VADER
        self.vader = SentimentIntensityAnalyzer()

    def keyword_score(self, text):
        text_lower = text.lower()
        score = 0
        matches = 0
        for event, weight in self.event_weights.items():
            if event in text_lower:
                score += weight
                matches += 1
        
        if matches == 0:
            return 0
        return max(min(score / matches, 1.0), -1.0)

    def finbert_score(self, text):
        if not self.finbert or not text.strip():
            return 0
            
        # Truncate text to avoid exceeding token limit (512 tokens)
        truncated_text = text[:1500]
        try:
            result = self.finbert(truncated_text)[0]
            label = result['label']
            score = result['score']
            
            if label == 'positive':
                return score
            elif label == 'negative':
                return -score
            else:
                return 0
        except Exception:
            return 0

    def vader_score(self, text):
        return self.vader.polarity_scores(text)['compound']

    def textblob_score(self, text):
        return TextBlob(text).sentiment.polarity

    def analyze(self, text):
        keyword = self.keyword_score(text)
        finbert = self.finbert_score(text)
        vader = self.vader_score(text)
        textblob = self.textblob_score(text)
        
        # As per the prompt formula:
        # Final Score = (Keyword × 0.40) + (Financial × 0.25) + (Numerical × 0.20) + (Context × 0.15)
        # Since we use 4 models, we adapt it to: Keyword (40%), FinBERT (30%), VADER (20%), TextBlob (10%)
        final_score = (keyword * 0.40) + (finbert * 0.30) + (vader * 0.20) + (textblob * 0.10)
        
        # Normalize
        final_score = max(min(final_score, 1.0), -1.0)
        
        if final_score >= 0.15:
            classification = "Positive"
        elif final_score <= -0.15:
            classification = "Negative"
        else:
            classification = "Neutral"
            
        return {
            "score": round(final_score, 4),
            "classification": classification,
            "components": {
                "keyword": round(keyword, 4),
                "finbert": round(finbert, 4),
                "vader": round(vader, 4),
                "textblob": round(textblob, 4)
            }
        }
