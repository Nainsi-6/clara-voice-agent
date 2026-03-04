#!/usr/bin/env python3
"""
Clara Automation Pipeline - Project Validation & Summary
Validates that all required files exist and shows project structure.
"""

import os
import json
from pathlib import Path

def validate_project():
    """Validate project structure and files."""
    
    # Use current working directory where files are extracted
    project_root = os.getcwd()
    
    print("=" * 80)
    print("CLARA AUTOMATION PIPELINE - PROJECT VALIDATION")
    print("=" * 80)
    print(f"Project Root: {project_root}")
    print(f"Root Exists: {os.path.exists(project_root)}\n")
    
    # Define required files
    required_files = {
        "Core Modules": [
            "schemas.py",
            "extractor.py",
            "prompt_generator.py",
            "patcher.py",
            "pipeline.py",
            "batch_processor.py",
            "app.py",
        ],
        "Scripts": [
            "quickstart.py",
            "validate_project.py",
        ],
        "Configuration": [
            "requirements.txt",
        ],
        "Documentation": [
            "README.md",
        ],
        "Sample Data": [
            "sample_transcripts/demo_001.txt",
            "sample_transcripts/onboarding_001.txt",
        ]
    }
    
    # Check files
    all_good = True
    for category, files in required_files.items():
        print(f"\n{category}:")
        print("-" * 40)
        
        for file in files:
            filepath = os.path.join(project_root, file)
            exists = os.path.exists(filepath) and os.path.isfile(filepath)
            status = "✓" if exists else "✗"
            
            print(f"  {status} {file}")
            if not exists:
                all_good = False
    
    # Show outputs directory
    print("\n\nOutput Directories:")
    print("-" * 40)
    outputs_dir = os.path.join(project_root, "outputs")
    
    if os.path.exists(outputs_dir):
        accounts_dir = os.path.join(outputs_dir, "accounts")
        if os.path.exists(accounts_dir):
            accounts = os.listdir(accounts_dir)
            print(f"  ✓ outputs/accounts/ ({len(accounts)} accounts)")
            
            for account in sorted(accounts):
                account_path = os.path.join(accounts_dir, account)
                if os.path.isdir(account_path):
                    v1_exists = os.path.exists(os.path.join(account_path, "v1"))
                    v2_exists = os.path.exists(os.path.join(account_path, "v2"))
                    changelog_exists = os.path.exists(os.path.join(account_path, "changelog.json"))
                    
                    v1_status = "✓" if v1_exists else "✗"
                    v2_status = "✓" if v2_exists else "✗"
                    cl_status = "✓" if changelog_exists else "✗"
                    
                    print(f"    └─ {account}/")
                    print(f"       {v1_status} v1/ {v2_status} v2/ {cl_status} changelog.json")
        else:
            print(f"  - outputs/accounts/ (not yet created)")
    else:
        print(f"  - outputs/ (will be created on first run)")
    
    # Final summary
    print("\n" + "=" * 80)
    if all_good:
        print("✓ PROJECT VALIDATION PASSED")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Run demo: python quickstart.py")
        print("  3. View UI: streamlit run app.py")
        print("  4. Batch process: python batch_processor.py ./sample_transcripts")
        print("\nFor detailed documentation, see: README.md")
    else:
        print("✗ PROJECT VALIDATION FAILED")
        print("Some required files are missing.")
    
    print("=" * 80)
    
    return all_good


if __name__ == "__main__":
    import sys
    success = validate_project()
    sys.exit(0 if success else 1)
