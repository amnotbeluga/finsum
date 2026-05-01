from summarizer import FinancialDocumentSummarizer

# Quick and simple usage
def quick_summarize(file_path):
    # Initialize with default model
    summarizer = FinancialDocumentSummarizer()
    
    # Read and summarize
    text = summarizer.read_document(file_path)
    summary = summarizer.summarize(text, max_length=200)
    
    print(f"Summary:\n{summary}")
    return summary

# Example
if __name__ == "__main__":
    quick_summarize("your_financial_document.pdf")