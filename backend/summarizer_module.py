import re
import nltk
from transformers import pipeline
from concurrent.futures import ThreadPoolExecutor, as_completed

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

        # Jaccard similarity threshold for deduplication
        self.dedup_threshold = 0.85

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

    # ─────────────────── Jaccard Similarity Deduplication ─────────────────────
    def jaccard_similarity(self, s1, s2):
        set1 = set(s1.lower().split())
        set2 = set(s2.lower().split())
        if not set1 or not set2:
            return 0.0
        intersection = set1 & set2
        union = set1 | set2
        return len(intersection) / len(union)

    def deduplicate_across_categories(self, summary):
        all_texts = []
        for cat, text in summary.items():
            all_texts.append((cat, text))

        # Compare every pair and remove near-duplicates
        to_remove = set()
        for i in range(len(all_texts)):
            for j in range(i + 1, len(all_texts)):
                sim = self.jaccard_similarity(all_texts[i][1], all_texts[j][1])
                if sim >= self.dedup_threshold:
                    # Keep the one from the more specific category, remove "other" first
                    if all_texts[j][0] == "other":
                        to_remove.add(all_texts[j][0])
                    elif all_texts[i][0] == "other":
                        to_remove.add(all_texts[i][0])
                    else:
                        to_remove.add(all_texts[j][0])

        for cat in to_remove:
            if cat in summary:
                del summary[cat]

        return summary

    # ─────────────────── BART Summarization ───────────────────────────────────
    def bart_summarize(self, text):
        if not self.bart or len(text.split()) < 30:
            return text

        truncated = " ".join(text.split()[:1000])
        try:
            res = self.bart(truncated, max_length=130, min_length=30, do_sample=False)
            return res[0]['summary_text']
        except Exception:
            return text

    # ─────────────────── Parallel Category Summarization ──────────────────────
    def _summarize_category(self, cat, sents):
        if cat == "other":
            return None, None
        selected = self.score_and_select(sents, limit=5)
        if not selected:
            return None, None

        combined = " ".join(selected)
        if len(combined.split()) > 60:
            result = self.bart_summarize(combined)
        else:
            result = combined

        return cat, result

    def process(self, raw_text):
        sentences = self.clean_and_split(raw_text)
        categorized = self.categorize_sentences(sentences)

        summary = {}

        # Parallel processing with ThreadPoolExecutor (4 workers)
        tasks = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            for cat, sents in categorized.items():
                if sents:
                    tasks.append(executor.submit(self._summarize_category, cat, sents))

            for future in as_completed(tasks):
                try:
                    cat, result = future.result()
                    if cat and result:
                        summary[cat] = result
                except Exception:
                    pass

        # Jaccard deduplication across all categories
        summary = self.deduplicate_across_categories(summary)

        return summary
