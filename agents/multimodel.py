import os
import json
from datetime import datetime
from summarizer import FinancialDocumentSummarizer

class MultiModelSummarizer:
    def __init__(self, skip_pages=2):

        self.skip_pages = skip_pages
        self.models = {
            'BART': {
                'name': 'facebook/bart-large-cnn',
                'description': 'Good balance of quality and speed',
                'type': 'Balanced'
            },
            'PEGASUS': {
                'name': 'google/pegasus-xsum',
                'description': 'Better for news-style summaries',
                'type': 'Concise'
            },
            'T5': {
                'name': 't5-large',
                'description': 'Versatile model',
                'type': 'Detailed'
            },
            'DistilBART': {
                'name': 'sshleifer/distilbart-cnn-12-6',
                'description': 'Faster, slightly less accurate',
                'type': 'Fast'
            }
        }
    
    def process_with_all_models(self, document_path, output_dir="summaries"):
        """
        Process a single document with all available models
        
        Args:
            document_path: Path to the financial document
            output_dir: Directory to save summaries
        """
        if not os.path.exists(document_path):
            print(f"Error: Document not found at {document_path}")
            return
        
        print("="*70)
        print(f"MULTI-MODEL FINANCIAL DOCUMENT SUMMARIZER")
        print("="*70)
        print(f"Document: {os.path.basename(document_path)}")
        print(f"Total models: {len(self.models)}")
        print("="*70)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp for this batch
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc_name = os.path.splitext(os.path.basename(document_path))[0]
        
        results = {}
        
        # Process with each model
        for model_key, model_info in self.models.items():
            print(f"\n{'='*50}")
            print(f"Processing with {model_key} model...")
            print(f"Type: {model_info['type']}")
            print(f"Model: {model_info['name']}")
            print(f"Description: {model_info['description']}")
            print(f"{'='*50}")
            
            try:
                # Initialize summarizer with current model
                summarizer = FinancialDocumentSummarizer(
                    model_name=model_info['name'],
                    skip_pages=self.skip_pages
                )
                
                # Generate summary
                report = summarizer.generate_comprehensive_summary(document_path)
                
                # Store results
                results[model_key] = {
                    'info': model_info,
                    'report': report
                }
                
                # Save individual model summary
                self._save_individual_summary(
                    report, 
                    model_key, 
                    output_dir, 
                    doc_name, 
                    timestamp
                )
                
                # Display summary preview
                self._display_summary_preview(model_key, report)
                
            except Exception as e:
                print(f"Error processing with {model_key}: {e}")
                results[model_key] = {
                    'info': model_info,
                    'error': str(e)
                }
        
        # Save comparison report
        self._save_comparison_report(results, output_dir, doc_name, timestamp)
        
        return results
    
    def process_with_selected_models(self, document_path, selected_models, output_dir="summaries"):
        """
        Process document with selected models only
        
        Args:
            document_path: Path to the financial document
            selected_models: List of model keys (e.g., ['BART', 'T5'])
            output_dir: Directory to save summaries
        """
        valid_models = [m for m in selected_models if m in self.models]
        
        if not valid_models:
            print("No valid models selected.")
            return
        
        print(f"\nProcessing with selected models: {', '.join(valid_models)}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc_name = os.path.splitext(os.path.basename(document_path))[0]
        
        results = {}
        
        for model_key in valid_models:
            model_info = self.models[model_key]
            print(f"\n{'='*40}")
            print(f"Processing with {model_key}...")
            
            try:
                summarizer = FinancialDocumentSummarizer(
                    model_name=model_info['name'],
                    skip_pages=self.skip_pages
                )
                
                report = summarizer.generate_comprehensive_summary(document_path)
                
                results[model_key] = {
                    'info': model_info,
                    'report': report
                }
                
                # Save individual summary
                self._save_individual_summary(
                    report, 
                    model_key, 
                    output_dir, 
                    doc_name, 
                    timestamp
                )
                
            except Exception as e:
                print(f"Error: {e}")
                results[model_key] = {'info': model_info, 'error': str(e)}
        
        return results
    
    def _save_individual_summary(self, report, model_key, output_dir, doc_name, timestamp):
        """Save individual model summary to file"""
        if report.get('error'):
            return
        
        # Create filename
        filename = f"{doc_name}_{model_key}_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write(f"FINANCIAL DOCUMENT SUMMARY - {model_key} MODEL\n")
            f.write("="*60 + "\n\n")
            f.write(f"Document: {report['file_name']}\n")
            f.write(f"Model: {model_key}\n")
            f.write(f"Model Type: {self.models[model_key]['type']}\n")
            f.write(f"Description: {self.models[model_key]['description']}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("-"*60 + "\n")
            f.write("DOCUMENT INFO:\n")
            f.write("-"*60 + "\n")
            f.write(f"Size: {report['file_size']}\n")
            f.write(f"Original Length: {report['document_length']}\n")
            f.write(f"Summary Length: {report['summary_word_count']} words\n\n")
            
            f.write("-"*60 + "\n")
            f.write("SUMMARY:\n")
            f.write("-"*60 + "\n")
            f.write(report['summary'] + "\n\n")
        
        print(f"  ✓ Saved: {filename}")
    
    def _save_comparison_report(self, results, output_dir, doc_name, timestamp):
        """Save a comparison report of all models"""
        filename = f"{doc_name}_model_comparison_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("MULTI-MODEL FINANCIAL DOCUMENT SUMMARY COMPARISON\n")
            f.write("="*70 + "\n\n")
            f.write(f"Document: {doc_name}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Models compared: {len([r for r in results.values() if 'report' in r])}\n\n")
            
            # Summary statistics
            f.write("-"*70 + "\n")
            f.write("SUMMARY STATISTICS:\n")
            f.write("-"*70 + "\n")
            
            for model_key, result in results.items():
                if 'report' in result:
                    report = result['report']
                    f.write(f"\n{model_key} ({result['info']['type']}):\n")
                    f.write(f"  - Summary Length: {report['summary_word_count']} words\n")
                    f.write(f"  - Compression: {report['summary_word_count']/int(report['document_length'].split()[0]):.1%}\n")
            
            # Side-by-side summaries
            f.write("\n" + "="*70 + "\n")
            f.write("SIDE-BY-SIDE SUMMARY COMPARISON:\n")
            f.write("="*70 + "\n\n")
            
            for model_key, result in results.items():
                if 'report' in result:
                    f.write(f"\n{'*'*50}\n")
                    f.write(f"{model_key} MODEL - {result['info']['type']}\n")
                    f.write(f"{'*'*50}\n")
                    f.write(result['report']['summary'] + "\n")
                    f.write(f"\nHighlights ({len(result['report']['financial_highlights'])}):\n")
                    for highlight in result['report']['financial_highlights'][:3]:  # Top 3 highlights
                        f.write(f"  • {highlight}\n")
            
            # JSON version for programmatic access
            f.write("\n" + "="*70 + "\n")
            f.write("JSON DATA (for programmatic access):\n")
            f.write("="*70 + "\n\n")
            
            json_data = {}
            for model_key, result in results.items():
                if 'report' in result:
                    json_data[model_key] = {
                        'type': result['info']['type'],
                        'summary': result['report']['summary'],
                        'summary_length': result['report']['summary_word_count'],
                        'highlights': result['report']['financial_highlights']
                    }
            
            f.write(json.dumps(json_data, indent=2))
        
        print(f"\n✓ Comparison report saved: {filename}")
    
    def _display_summary_preview(self, model_key, report):
        """Display a preview of the summary"""
        print(f"\n{model_key} SUMMARY PREVIEW:")
        print("-" * 40)
        print(f"Length: {report['summary_word_count']} words")
        print(f"First 200 chars: {report['summary'][:200]}...")
        print(f"Highlights found: {len(report['financial_highlights'])}")

def main():
    """Main function to run the multi-model summarizer"""
    
    # Get document path
    document_path = input("Enter the path to your financial document: ").strip()
    
    if not os.path.exists(document_path):
        print(f"Error: File not found: {document_path}")
        return
    
    # Ask for processing mode
    print("\nSelect processing mode:")
    print("1. Process with ALL models")
    print("2. Select specific models")
    print("3. Quick comparison (BART + DistilBART only)")
    
    mode = input("Enter choice (1-3) [default: 1]: ").strip() or "1"
    
    # Ask for pages to skip
    skip_pages = input("\nNumber of pages to skip [default: 2]: ").strip()
    skip_pages = int(skip_pages) if skip_pages.isdigit() else 2
    
    # Initialize multi-model summarizer
    multi_summarizer = MultiModelSummarizer(skip_pages=skip_pages)
    
    # Process based on mode
    if mode == "1":
        # Process with all models
        results = multi_summarizer.process_with_all_models(document_path)
        
    elif mode == "2":
        # Show available models
        print("\nAvailable models:")
        for i, (key, info) in enumerate(multi_summarizer.models.items(), 1):
            print(f"  {i}. {key} - {info['description']}")
        
        # Get user selection
        selection = input("\nEnter model numbers to use (comma-separated, e.g., 1,3): ").strip()
        selected_indices = [int(x.strip()) for x in selection.split(',') if x.strip().isdigit()]
        
        model_keys = list(multi_summarizer.models.keys())
        selected_models = [model_keys[i-1] for i in selected_indices if 1 <= i <= len(model_keys)]
        
        if selected_models:
            results = multi_summarizer.process_with_selected_models(document_path, selected_models)
        else:
            print("No valid models selected.")
            return
            
    else:  # mode "3"
        # Quick comparison
        selected_models = ['BART', 'DistilBART']
        results = multi_summarizer.process_with_selected_models(document_path, selected_models)
    
    print("\n" + "="*70)
    print("PROCESSING COMPLETE!")
    print("="*70)
    print(f"\nAll summaries saved in the 'summaries' directory")

if __name__ == "__main__":
    main()