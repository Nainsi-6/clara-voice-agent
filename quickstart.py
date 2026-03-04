#!/usr/bin/env python3
"""
Quick Start Demo: Run the pipeline on sample transcripts end-to-end.
No configuration needed - just run!
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
sys.path.insert(0, current_dir)

from pipeline import PipelineOrchestrator


def main():
    print("=" * 80)
    print("CLARA AUTOMATION PIPELINE - QUICK START DEMO")
    print("=" * 80)
    
    # Initialize pipeline
    orchestrator = PipelineOrchestrator()
    
    # Sample data directory
    script_dir = Path(current_dir)
    sample_dir = script_dir / "sample_transcripts"
    
    if not sample_dir.exists():
        print(f"\n✗ Error: Sample transcripts directory not found: {sample_dir}")
        sys.exit(1)
    
    # Check for sample files
    demo_file = sample_dir / "demo_001.txt"
    onboarding_file = sample_dir / "onboarding_001.txt"
    
    if not demo_file.exists():
        print(f"\n✗ Error: Demo file not found: {demo_file}")
        sys.exit(1)
    
    if not onboarding_file.exists():
        print(f"\n✗ Error: Onboarding file not found: {onboarding_file}")
        sys.exit(1)
    
    # PHASE 1: Process demo call
    print("\n" + "=" * 80)
    print("PHASE 1: DEMO CALL PROCESSING")
    print("=" * 80)
    
    try:
        with open(demo_file, 'r') as f:
            demo_transcript = f.read()
        
        print(f"\nReading: {demo_file}")
        print(f"Transcript length: {len(demo_transcript)} chars")
        
        print("\n→ Processing demo call...")
        account_id, summary = orchestrator.process_demo_call(
            demo_transcript,
            account_id="acc_fireguard_001",
            company_name="FireGuard Protection Services"
        )
        
        print(f"\n✓ SUCCESS: v1 created")
        print(f"  Company: {summary['company_name']}")
        print(f"  Account: {summary['account_id']}")
        print(f"  Version: {summary['version']}")
        print(f"  Output dir: {Path(summary['account_memo_path']).parent}")
        print(f"  Unknowns flagged: {summary['unknowns_count']}")
        
    except Exception as e:
        print(f"\n✗ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # PHASE 2: Process onboarding call
    print("\n" + "=" * 80)
    print("PHASE 2: ONBOARDING CALL PROCESSING")
    print("=" * 80)
    
    try:
        with open(onboarding_file, 'r') as f:
            onboarding_transcript = f.read()
        
        print(f"\nReading: {onboarding_file}")
        print(f"Transcript length: {len(onboarding_transcript)} chars")
        
        print("\n→ Processing onboarding call...")
        account_id, summary = orchestrator.process_onboarding_call(
            onboarding_transcript,
            account_id="acc_fireguard_001"
        )
        
        print(f"\n✓ SUCCESS: v2 created with changelog")
        print(f"  Company: {summary['company_name']}")
        print(f"  Account: {summary['account_id']}")
        print(f"  Version: {summary['version']}")
        print(f"  Output dir: {Path(summary['account_memo_path']).parent}")
        print(f"  Changes logged: {summary['changes_count']}")
        print(f"  Unknowns remaining: {summary['unknowns_remaining']}")
        
    except Exception as e:
        print(f"\n✗ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # PHASE 3: Summary
    print("\n" + "=" * 80)
    print("COMPLETION SUMMARY")
    print("=" * 80)
    
    status = orchestrator.get_account_status("acc_fireguard_001")
    
    print(f"\nAccount Status: acc_fireguard_001")
    print(f"  v1 Exists: {status['v1_exists']} ✓")
    print(f"  v2 Exists: {status['v2_exists']} ✓")
    print(f"  Changelog Exists: {status['changelog_exists']} ✓")
    print(f"  Total Changes: {status.get('changes_count', 0)}")
    
    print(f"\nOutput Location:")
    print(f"  {Path(orchestrator.base_output_dir) / 'accounts' / 'acc_fireguard_001'}/")
    print(f"    ├── v1/")
    print(f"    │   ├── account_memo.json")
    print(f"    │   ├── agent_spec.json")
    print(f"    │   ├── system_prompt.txt")
    print(f"    │   ├── transfer_protocol.txt")
    print(f"    │   ├── fallback_protocol.txt")
    print(f"    │   └── unknowns.txt")
    print(f"    ├── v2/")
    print(f"    │   ├── account_memo.json")
    print(f"    │   ├── agent_spec.json")
    print(f"    │   ├── system_prompt.txt")
    print(f"    │   ├── transfer_protocol.txt")
    print(f"    │   ├── fallback_protocol.txt")
    print(f"    │   └── unknowns.txt")
    print(f"    └── changelog.json & changelog.txt")
    
    print("\n" + "=" * 80)
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. View outputs: Open any .json file in outputs/accounts/acc_fireguard_001/")
    print("  2. View changelog: cat outputs/accounts/acc_fireguard_001/changelog.txt")
    print("  3. Run UI: streamlit run app.py")
    print("  4. Batch process: python batch_processor.py ./sample_transcripts")
    print("\nFor details, see: README.md")


if __name__ == "__main__":
    main()
