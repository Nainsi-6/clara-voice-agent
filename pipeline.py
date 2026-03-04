"""
Main Pipeline Orchestrator: Coordinates extraction, generation, and patching.
Handles file I/O, versioning, and idempotency.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from schemas import AccountMemo, RetellAgentSpec, Changelog
from extractor import TranscriptExtractor
from prompt_generator import PromptGenerator
from patcher import PatchApplier


class PipelineOrchestrator:
    """
    Main orchestrator for Clara automation pipeline.
    Handles v1 creation from demo transcripts and v2 creation from onboarding.
    """
    
    # def __init__(self, base_output_dir: str = "/vercel/share/v0-project/outputs"):
    #     self.base_output_dir = Path(base_output_dir)
    #     self.base_output_dir.mkdir(parents=True, exist_ok=True)
    #     self.extractor = TranscriptExtractor()
    #     self.prompt_gen = PromptGenerator()
    #     self.patcher = PatchApplier()

    def __init__(self, base_output_dir: Optional[str] = None):
        # Use project root directory if no path provided
        if base_output_dir is None:
            project_root = Path(__file__).resolve().parent
            base_output_dir = project_root / "outputs"

        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

        self.extractor = TranscriptExtractor()
        self.prompt_gen = PromptGenerator()
        self.patcher = PatchApplier()
    
    def process_demo_call(self, 
                         transcript: str,
                         account_id: str,
                         company_name: Optional[str] = None) -> Tuple[str, dict]:
        """
        Process demo call transcript and generate v1 assets.
        Returns: (account_id, output_summary)
        """
        
        print(f"\n[PIPELINE] Processing DEMO for account: {account_id}")
        
        # Extract account memo from demo
        memo = self.extractor.extract_account_memo(transcript, call_type="demo", account_id=account_id)
        if company_name:
            memo.company_name = company_name
        
        # Generate Retell agent spec v1
        agent_spec = self.prompt_gen.generate_agent_spec(memo, version="v1")
        
        # Create output directories
        account_dir = self.base_output_dir / "accounts" / account_id
        v1_dir = account_dir / "v1"
        v1_dir.mkdir(parents=True, exist_ok=True)
        
        # Save v1 account memo
        memo_path = v1_dir / "account_memo.json"
        self._save_json(memo.to_dict(), memo_path)
        
        # Save v1 agent spec
        agent_path = v1_dir / "agent_spec.json"
        self._save_json(agent_spec.to_dict(), agent_path)
        
        # Save system prompt as readable file
        prompt_path = v1_dir / "system_prompt.txt"
        self._save_text(agent_spec.system_prompt, prompt_path)
        
        # Save transfer protocol
        transfer_path = v1_dir / "transfer_protocol.txt"
        self._save_text(agent_spec.call_transfer_protocol, transfer_path)
        
        # Save fallback protocol
        fallback_path = v1_dir / "fallback_protocol.txt"
        self._save_text(agent_spec.fallback_protocol, fallback_path)
        
        # Save extraction summary with unknowns
        if memo.questions_or_unknowns:
            unknowns_path = v1_dir / "unknowns.txt"
            self._save_text("\n".join(memo.questions_or_unknowns), unknowns_path)
        
        summary = {
            "account_id": account_id,
            "version": "v1",
            "stage": "demo",
            "company_name": memo.company_name,
            "account_memo_path": str(memo_path),
            "agent_spec_path": str(agent_path),
            "system_prompt_path": str(prompt_path),
            "unknowns_count": len(memo.questions_or_unknowns),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        print(f"[DEMO] ✓ Created v1 for {memo.company_name}")
        print(f"[DEMO] Output: {v1_dir}")
        if memo.questions_or_unknowns:
            print(f"[DEMO] ⚠ {len(memo.questions_or_unknowns)} unknowns identified")
        
        return account_id, summary
    
    def process_onboarding_call(self,
                               transcript: str,
                               account_id: str) -> Tuple[str, dict]:
        """
        Process onboarding call transcript and apply patch to create v2.
        Returns: (account_id, output_summary)
        """
        
        print(f"\n[PIPELINE] Processing ONBOARDING for account: {account_id}")
        
        # Load existing v1 memo
        account_dir = self.base_output_dir / "accounts" / account_id
        v1_memo_path = account_dir / "v1" / "account_memo.json"
        
        if not v1_memo_path.exists():
            raise FileNotFoundError(f"v1 memo not found: {v1_memo_path}")
        
        v1_memo_data = self._load_json(v1_memo_path)
        v1_memo = AccountMemo.from_dict(v1_memo_data)
        
        # Apply onboarding patch
        v2_memo, changelog = self.patcher.apply_onboarding_patch(
            v1_memo,
            transcript,
            account_id
        )
        
        # Generate v2 agent spec
        v2_agent_spec = self.prompt_gen.generate_agent_spec(v2_memo, version="v2")
        
        # Create v2 directory
        v2_dir = account_dir / "v2"
        v2_dir.mkdir(parents=True, exist_ok=True)
        
        # Save v2 account memo
        memo_path = v2_dir / "account_memo.json"
        self._save_json(v2_memo.to_dict(), memo_path)
        
        # Save v2 agent spec
        agent_path = v2_dir / "agent_spec.json"
        self._save_json(v2_agent_spec.to_dict(), agent_path)
        
        # Save v2 system prompt
        prompt_path = v2_dir / "system_prompt.txt"
        self._save_text(v2_agent_spec.system_prompt, prompt_path)
        
        # Save v2 protocols
        transfer_path = v2_dir / "transfer_protocol.txt"
        self._save_text(v2_agent_spec.call_transfer_protocol, transfer_path)
        
        fallback_path = v2_dir / "fallback_protocol.txt"
        self._save_text(v2_agent_spec.fallback_protocol, fallback_path)
        
        # Save changelog
        changelog_path = account_dir / "changelog.json"
        self._save_json(changelog.to_dict(), changelog_path)
        
        # Save human-readable changelog
        changelog_text_path = account_dir / "changelog.txt"
        summary_text = self.patcher.generate_changelog_summary(changelog)
        self._save_text(summary_text, changelog_text_path)
        
        # Save remaining unknowns
        if v2_memo.questions_or_unknowns:
            unknowns_path = v2_dir / "unknowns.txt"
            self._save_text("\n".join(v2_memo.questions_or_unknowns), unknowns_path)
        
        summary = {
            "account_id": account_id,
            "version": "v2",
            "stage": "onboarding",
            "company_name": v2_memo.company_name,
            "account_memo_path": str(memo_path),
            "agent_spec_path": str(agent_path),
            "changelog_path": str(changelog_path),
            "changes_count": len(changelog.entries),
            "unknowns_remaining": len(v2_memo.questions_or_unknowns),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        print(f"[ONBOARDING] ✓ Created v2 for {v2_memo.company_name}")
        print(f"[ONBOARDING] Changes: {len(changelog.entries)}")
        print(f"[ONBOARDING] Output: {v2_dir}")
        
        return account_id, summary
    
    def _save_json(self, data: dict, path: Path):
        """Save data as formatted JSON."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    
    def _load_json(self, path: Path) -> dict:
        """Load JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_text(self, text: str, path: Path):
        """Save text file."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
    
    def get_account_status(self, account_id: str) -> dict:
        """Get current status of an account."""
        account_dir = self.base_output_dir / "accounts" / account_id
        
        status = {
            "account_id": account_id,
            "v1_exists": (account_dir / "v1").exists(),
            "v2_exists": (account_dir / "v2").exists(),
            "changelog_exists": (account_dir / "changelog.json").exists(),
        }
        
        # Load v1 if exists
        v1_memo_path = account_dir / "v1" / "account_memo.json"
        if v1_memo_path.exists():
            data = self._load_json(v1_memo_path)
            status["v1_company"] = data.get("company_name")
            status["v1_timestamp"] = data.get("created_at")
        
        # Load v2 if exists
        v2_memo_path = account_dir / "v2" / "account_memo.json"
        if v2_memo_path.exists():
            data = self._load_json(v2_memo_path)
            status["v2_company"] = data.get("company_name")
            status["v2_timestamp"] = data.get("created_at")
        
        # Load changelog if exists
        changelog_path = account_dir / "changelog.json"
        if changelog_path.exists():
            data = self._load_json(changelog_path)
            status["changes_count"] = len(data.get("entries", []))
        
        return status

