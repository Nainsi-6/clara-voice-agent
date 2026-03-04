"""
Batch Processor: Run pipeline on multiple demo + onboarding pairs.
Idempotent: safe to run multiple times.
"""

import os
import json
from pathlib import Path
from typing import List, Dict
from pipeline import PipelineOrchestrator


class BatchProcessor:
    """Process batches of demo and onboarding transcripts."""
    
    def __init__(self, transcripts_dir: str, output_dir: str = "/vercel/share/v0-project/outputs"):
        self.transcripts_dir = Path(transcripts_dir)
        self.output_dir = output_dir
        self.orchestrator = PipelineOrchestrator(output_dir)
        self.results = {
            "demo_processed": [],
            "demo_failed": [],
            "onboarding_processed": [],
            "onboarding_failed": [],
            "timestamp": None,
        }
    
    def process_all(self) -> Dict:
        """
        Process all transcripts in directory.
        Expects structure:
            transcripts/
            ├── demo_001.txt
            ├── demo_002.txt
            ├── onboarding_001.txt
            ├── onboarding_002.txt
        """
        
        print("=" * 80)
        print("CLARA AUTOMATION BATCH PROCESSOR")
        print("=" * 80)
        
        # Find all transcript files
        demo_files = sorted(self.transcripts_dir.glob("demo_*.txt"))
        onboarding_files = sorted(self.transcripts_dir.glob("onboarding_*.txt"))
        
        print(f"\nFound {len(demo_files)} demo transcripts")
        print(f"Found {len(onboarding_files)} onboarding transcripts")
        
        # Process demo calls
        print("\n" + "=" * 80)
        print("PHASE 1: PROCESSING DEMO CALLS")
        print("=" * 80)
        
        for demo_file in demo_files:
            self._process_demo_file(demo_file)
        
        # Process onboarding calls
        print("\n" + "=" * 80)
        print("PHASE 2: PROCESSING ONBOARDING CALLS")
        print("=" * 80)
        
        for onboarding_file in onboarding_files:
            self._process_onboarding_file(onboarding_file)
        
        # Generate summary
        self._print_summary()
        
        return self.results
    
    def _process_demo_file(self, filepath: Path):
        """Process single demo transcript file."""
        try:
            print(f"\n→ Processing: {filepath.name}")
            
            # Read transcript
            with open(filepath, 'r') as f:
                transcript = f.read()
            
            # Extract account ID from filename (demo_001.txt -> acc_001)
            filename_base = filepath.stem  # "demo_001"
            parts = filename_base.split("_")
            if len(parts) >= 2:
                account_suffix = "_".join(parts[1:])
                account_id = f"acc_{account_suffix}"
            else:
                account_id = f"acc_{filepath.stem}"
            
            # Run pipeline
            acc_id, summary = self.orchestrator.process_demo_call(
                transcript,
                account_id
            )
            
            self.results["demo_processed"].append(summary)
            print(f"✓ Success")
            
        except Exception as e:
            print(f"✗ Failed: {str(e)}")
            self.results["demo_failed"].append({
                "file": filepath.name,
                "error": str(e),
            })
    
    def _process_onboarding_file(self, filepath: Path):
        """Process single onboarding transcript file."""
        try:
            print(f"\n→ Processing: {filepath.name}")
            
            # Read transcript
            with open(filepath, 'r') as f:
                transcript = f.read()
            
            # Extract account ID from filename (onboarding_001.txt -> acc_001)
            filename_base = filepath.stem  # "onboarding_001"
            parts = filename_base.split("_")
            if len(parts) >= 2:
                account_suffix = "_".join(parts[1:])
                account_id = f"acc_{account_suffix}"
            else:
                account_id = f"acc_{filepath.stem}"
            
            # Check if v1 exists
            account_dir = Path(self.output_dir) / "accounts" / account_id
            if not (account_dir / "v1" / "account_memo.json").exists():
                raise FileNotFoundError(f"v1 not found for {account_id}. Run demo first.")
            
            # Run pipeline
            acc_id, summary = self.orchestrator.process_onboarding_call(
                transcript,
                account_id
            )
            
            self.results["onboarding_processed"].append(summary)
            print(f"✓ Success")
            
        except Exception as e:
            print(f"✗ Failed: {str(e)}")
            self.results["onboarding_failed"].append({
                "file": filepath.name,
                "error": str(e),
            })
    
    def _print_summary(self):
        """Print final summary."""
        print("\n" + "=" * 80)
        print("BATCH PROCESSING SUMMARY")
        print("=" * 80)
        
        demo_success = len(self.results["demo_processed"])
        demo_fail = len(self.results["demo_failed"])
        onboarding_success = len(self.results["onboarding_processed"])
        onboarding_fail = len(self.results["onboarding_failed"])
        
        print(f"\n✓ Demo calls processed: {demo_success}")
        if demo_fail:
            print(f"✗ Demo calls failed: {demo_fail}")
        
        print(f"\n✓ Onboarding calls processed: {onboarding_success}")
        if onboarding_fail:
            print(f"✗ Onboarding calls failed: {onboarding_fail}")
        
        total_accounts = demo_success
        fully_processed = sum(1 for d in self.results["demo_processed"]
                             if f"acc_{d.get('account_id', '').split('_')[-1]}" 
                             in [o.get('account_id') for o in self.results["onboarding_processed"]])
        
        print(f"\n📊 Total accounts: {total_accounts}")
        print(f"📊 Fully processed (demo + onboarding): {fully_processed}")
        
        print("\n✓ All outputs saved to: " + str(Path(self.output_dir) / "accounts"))
    
    def save_results(self, output_file: str = "batch_results.json"):
        """Save batch processing results."""
        from datetime import datetime
        self.results["timestamp"] = datetime.utcnow().isoformat()
        
        output_path = Path(self.output_dir).parent / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {output_path}")


def main():
    """CLI entry point for batch processing."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python batch_processor.py <transcripts_dir>")
        print("Example: python batch_processor.py ./sample_transcripts")
        sys.exit(1)
    
    transcripts_dir = sys.argv[1]
    
    if not Path(transcripts_dir).exists():
        print(f"Error: Directory not found: {transcripts_dir}")
        sys.exit(1)
    
    processor = BatchProcessor(transcripts_dir)
    results = processor.process_all()
    processor.save_results()


if __name__ == "__main__":
    main()
