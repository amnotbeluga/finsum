import re
import nltk
from transformers import pipeline

class SummarizerModule:
    def __init__(self):
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            
        try:
            self.bart = pipeline("summarization", model="facebook/bart-large-cnn")
        except Exception:
            self.bart = None

        self.categories = {
            "announcements": ["announce", "declare", "notify", "update"],
            "orders": ["order", "contract", "awarded", "bid"],
            "cases": ["litigation", "court", "lawsuit", "tribunal", "case"],
            "financial_results": ["quarter", "revenue", "profit", "ebitda", "margin", "result", "loss"],
            "corporate_actions": ["dividend", "split", "bonus", "merger", "acquisition"],
            "compliance": ["sebi", "compliance", "regulation", "filing", "statutory"]
        }

    def clean_and_split(self, text):
        # Remove page numbers, headers, disclaimers
        text = re.sub(r'\bPage \d+ of \d+\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Disclaimer.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\n+', ' ', text)
        
        try:
            sentences = nltk.sent_tokenize(text)
        except Exception:
            sentences = [s.strip() + '.' for s in re.split(r'[.!?]+', text) if s.strip()]
            
        return sentences

    def categorize_sentences(self, sentences):
        categorized = {k: [] for k in self.categories.keys()}
        categorized["other"] = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            matched = False
            for cat, keywords in self.categories.items():
                if any(kw in sentence_lower for kw in keywords):
                    categorized[cat].append(sentence)
                    matched = True
                    break
            if not matched:
                categorized["other"].append(sentence)
                
        return categorized

    def score_and_select(self, sentences, limit=5):
        scored = []
        for s in sentences:
            score = 0
            # Priority for numbers and key financial terms
            if re.search(r'\d+', s): score += 2
            if re.search(r'\b(Rs|Cr|Lakh|%|crore)\b', s, re.IGNORECASE): score += 3
            if re.search(r'\b(increase|decrease|growth|fall|rise)\b', s, re.IGNORECASE): score += 2
            scored.append((score, s))
            
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for score, s in scored[:limit]]

    def bart_summarize(self, text):
        if not self.bart or len(text.split()) < 30:
            return text
            
        truncated = " ".join(text.split()[:1000])
        try:
            res = self.bart(truncated, max_length=130, min_length=30, do_sample=False)
            return res[0]['summary_text']
        except Exception:
            return text

    def process(self, raw_text):
        sentences = self.clean_and_split(raw_text)
        categorized = self.categorize_sentences(sentences)
        
        summary = {}
        for cat, sents in categorized.items():
            if cat == "other": continue
            selected = self.score_and_select(sents, limit=5)
            if selected:
                combined = " ".join(selected)
                if len(combined.split()) > 60:
                    summary[cat] = self.bart_summarize(combined)
                else:
                    summary[cat] = combined
                    
        return summary
