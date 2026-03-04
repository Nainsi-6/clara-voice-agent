"""
Patch Application Engine: Apply onboarding updates to v1 -> v2.
Preserves version history, logs all changes, handles conflicts intelligently.
"""

from typing import Optional, Dict, Any
from schemas import AccountMemo, Changelog, ChangelogEntry
from extractor import TranscriptExtractor
# from prompt_generator import PromptGenerator
import copy


class PatchApplier:
    """
    Intelligent patcher for onboarding data.
    Rules:
    - Never overwrite unrelated fields
    - Preserve full version history
    - Log all changes explicitly
    - When onboarding contradicts demo, onboarding wins but old value preserved
    """
    
    def __init__(self):
        self.changelog = None
    
    def apply_onboarding_patch(self,
                              v1_memo: AccountMemo,
                              onboarding_transcript: str,
                              account_id: str) -> tuple[AccountMemo, Changelog]:
        """
        Apply onboarding updates to v1 memo, creating v2.
        Returns: (v2_memo, changelog)
        """
        
        # Initialize changelog
        self.changelog = Changelog(
            account_id=account_id,
            from_version="v1",
            to_version="v2"
        )
        
        # Extract new/updated fields from onboarding transcript
        extractor = TranscriptExtractor()
        onboarding_extract = extractor.extract_account_memo(
            onboarding_transcript,
            call_type="onboarding",
            account_id=account_id
        )
        
        # Create v2 as deep copy of v1
        v2_memo = copy.deepcopy(v1_memo)
        
        # Apply intelligent patching
        v2_memo = self._apply_field_patches(v2_memo, onboarding_extract, "onboarding")
        
        return v2_memo, self.changelog
    
    def _apply_field_patches(self,
                            v1_memo: AccountMemo,
                            updates: AccountMemo,
                            source: str) -> AccountMemo:
        """Apply individual field updates from onboarding."""
        
        # Company name (usually stable)
        # if updates.company_name and updates.company_name != "UNKNOWN":
        #     self._log_change(v1_memo, updates, "company_name", source)
        #     v1_memo.company_name = updates.company_name
        
        # Industry (usually stable)
        if updates.industry:
            self._log_change(v1_memo, updates, "industry", source)
            v1_memo.industry = updates.industry
        
        # Business hours (refined during onboarding)
        if updates.business_hours and self._has_business_hours_info(updates.business_hours):
            self._log_change(v1_memo, updates, "business_hours", source, 
                           reason="Onboarding provides exact business hours")
            v1_memo.business_hours = updates.business_hours
            self._resolve_unknown(v1_memo, "business_hours")
        
        # Office address (usually confirmed in onboarding)
        # if updates.office_address:
        #     self._log_change(v1_memo, updates, "office_address", source)
        #     v1_memo.office_address = updates.office_address

        if updates.office_address:
            self._log_change(v1_memo, updates, "office_address", source)
            v1_memo.office_address = updates.office_address
            self._resolve_unknown(v1_memo, "office_address")
        
        # Office phone (usually confirmed in onboarding)
        # if updates.office_phone:
        #     self._log_change(v1_memo, updates, "office_phone", source)
        #     v1_memo.office_phone = updates.office_phone

        if updates.office_phone:
            self._log_change(v1_memo, updates, "office_phone", source)
            v1_memo.office_phone = updates.office_phone
            self._resolve_unknown(v1_memo, "office_phone")
        
        # Services (usually confirmed, not added)
        # if updates.services_supported and len(updates.services_supported) > len(v1_memo.services_supported):
        #     self._log_change(v1_memo, updates, "services_supported", source)
        #     v1_memo.services_supported = updates.services_supported

        if updates.services_supported:
            for service in updates.services_supported:
                if service not in v1_memo.services_supported:
                    old_val = v1_memo.services_supported.copy()
                    v1_memo.services_supported.append(service)

                    self.changelog.add_change(
                        field="services_supported",
                        old_val=old_val,
                        new_val=v1_memo.services_supported,
                        source=source,
                        reason="Onboarding adds service"
                    )
        
        # Emergency definition (refined during onboarding)
        # if updates.emergency_definition and updates.emergency_definition != v1_memo.emergency_definition:
        #     self._log_change(v1_memo, updates, "emergency_definition", source,
        #                    reason="Onboarding clarifies emergency criteria")
        #     v1_memo.emergency_definition = updates.emergency_definition
        
        # if updates.emergency_definition:
        #     for trigger in updates.emergency_definition:
        #         if trigger not in v1_memo.emergency_definition:
        #             old_val = v1_memo.emergency_definition.copy()
        #             v1_memo.emergency_definition.append(trigger)

        #             self.changelog.add_change(
        #                 field="emergency_definition",
        #                 old_val=old_val,
        #                 new_val=v1_memo.emergency_definition,
        #                 source=source,
        #                 reason="Onboarding clarifies emergency criteria"
        #             )

        if updates.emergency_definition:
            merged = list(set(v1_memo.emergency_definition + updates.emergency_definition))
            
            if set(merged) != set(v1_memo.emergency_definition):
                old_val = v1_memo.emergency_definition.copy()
                v1_memo.emergency_definition = merged

                self.changelog.add_change(
                    field="emergency_definition",
                    old_val=old_val,
                    new_val=merged,
                    source=source,
                    reason="Onboarding clarifies emergency criteria"
                )
                

        # Emergency routing (critical to get right from onboarding)
        if updates.emergency_routing_rules and len(updates.emergency_routing_rules) > 0:
            self._log_change(v1_memo, updates, "emergency_routing_rules", source,
                           reason="Onboarding specifies exact emergency routing")
            v1_memo.emergency_routing_rules = updates.emergency_routing_rules
        
        # Non-emergency routing (usually defined in onboarding)
        if updates.non_emergency_routing_rules and len(updates.non_emergency_routing_rules) > 0:
            self._log_change(v1_memo, updates, "non_emergency_routing_rules", source,
                           reason="Onboarding specifies after-hours handling")
            v1_memo.non_emergency_routing_rules = updates.non_emergency_routing_rules
        
        # Call transfer timeout (often clarified in onboarding)
        # if updates.call_transfer_timeout_seconds:
        #     self._log_change(v1_memo, updates, "call_transfer_timeout_seconds", source)
        #     v1_memo.call_transfer_timeout_seconds = updates.call_transfer_timeout_seconds

        if updates.call_transfer_timeout_seconds:
            self._log_change(v1_memo, updates, "call_transfer_timeout_seconds", source)
            v1_memo.call_transfer_timeout_seconds = updates.call_transfer_timeout_seconds
            self._resolve_unknown(v1_memo, "call_transfer_timeout")
        
        # Call transfer retries
        if updates.call_transfer_retries:
            self._log_change(v1_memo, updates, "call_transfer_retries", source)
            v1_memo.call_transfer_retries = updates.call_transfer_retries
        
        # Integration constraints (critical from onboarding)
        # if updates.integration_constraints and len(updates.integration_constraints) > 0:
        #     self._log_change(v1_memo, updates, "integration_constraints", source,
        #                    reason="Onboarding clarifies integration rules")
        #     v1_memo.integration_constraints = updates.integration_constraints

        if updates.integration_constraints:
            for constraint in updates.integration_constraints:
                if constraint not in v1_memo.integration_constraints:
                    old_val = v1_memo.integration_constraints.copy()
                    v1_memo.integration_constraints.append(constraint)

                    self.changelog.add_change(
                        field="integration_constraints",
                        old_val=old_val,
                        new_val=v1_memo.integration_constraints,
                        source=source,
                        reason="Onboarding adds integration constraint"
                    )
        
        # After hours flow (usually defined in onboarding)
        if updates.after_hours_flow_summary:
            self._log_change(v1_memo, updates, "after_hours_flow_summary", source)
            v1_memo.after_hours_flow_summary = updates.after_hours_flow_summary
        
        # Office hours flow (usually defined in onboarding)
        if updates.office_hours_flow_summary:
            self._log_change(v1_memo, updates, "office_hours_flow_summary", source)
            v1_memo.office_hours_flow_summary = updates.office_hours_flow_summary
        
        # Merge unknowns (keep both v1 and v2 unknowns)
        # if updates.questions_or_unknowns:
        #     for unknown in updates.questions_or_unknowns:
        #         if unknown not in v1_memo.questions_or_unknowns:
        #             v1_memo.questions_or_unknowns.append(unknown)

        # Remove resolved unknowns
        # resolved_fields = []

        # if updates.office_phone and "office_phone: phone number not provided" in v1_memo.questions_or_unknowns:
        #     v1_memo.questions_or_unknowns.remove("office_phone: phone number not provided")
        #     resolved_fields.append("office_phone")

        # if updates.office_address and "office_address: specific address not provided in transcript" in v1_memo.questions_or_unknowns:
        #     v1_memo.questions_or_unknowns.remove("office_address: specific address not provided in transcript")
        #     resolved_fields.append("office_address")

        # Add new unknowns from onboarding
        if updates.questions_or_unknowns:
            for unknown in updates.questions_or_unknowns:
                if unknown not in v1_memo.questions_or_unknowns:
                    v1_memo.questions_or_unknowns.append(unknown)
        
        # Notes
        # if updates.notes:
        #     if v1_memo.notes:
        #         v1_memo.notes += f" | Onboarding: {updates.notes}"
        #     else:
        #         v1_memo.notes = updates.notes

        if updates.notes:
            if v1_memo.notes:
                if updates.notes not in v1_memo.notes:
                    v1_memo.notes += f" | Onboarding: {updates.notes}"
            else:
                v1_memo.notes = updates.notes

        # Ensure deterministic timeout
        if not v1_memo.call_transfer_timeout_seconds:
            v1_memo.call_transfer_timeout_seconds = 30
        
        return v1_memo
    
    def _log_change(self,
                   old_memo: AccountMemo,
                   new_data: AccountMemo,
                   field_name: str,
                   source: str,
                   reason: Optional[str] = None):
        """Log a single field change in changelog."""
        
        old_value = getattr(old_memo, field_name, None)
        new_value = getattr(new_data, field_name, None)
        
        # Only log if actually changed
        if old_value != new_value:
            if old_value and new_value and not reason:
                reason = "Onboarding overrides demo assumption"
            self.changelog.add_change(
                field=field_name,
                old_val=old_value,
                new_val=new_value,
                source=source,
                reason=reason
            )
    
    def _has_business_hours_info(self, bh) -> bool:
        """Check if BusinessHours object has substantive info."""
        if bh.timezone:
            return True
        if any([bh.monday_start, bh.tuesday_start, bh.wednesday_start,
                bh.thursday_start, bh.friday_start]):
            return True
        return False
    
    def _resolve_unknown(self, memo: AccountMemo, field_prefix: str):
        """Remove resolved unknown entries when onboarding provides value."""
        memo.questions_or_unknowns = [
            u for u in memo.questions_or_unknowns
            if not u.startswith(field_prefix)
        ]
    
    def generate_changelog_summary(self, changelog: Changelog) -> str:
        """Generate human-readable changelog summary."""
        
        if not changelog.entries:
            return "No changes between v1 and v2"
        
        summary = f"Changelog: v1 → v2\n"
        summary += f"Account: {changelog.account_id}\n"
        summary += f"Updated: {changelog.created_at}\n"
        summary += f"Total Changes: {len(changelog.entries)}\n\n"
        
        for entry in changelog.entries:
            summary += f"Field: {entry.field_name}\n"
            summary += f"  Old: {entry.old_value}\n"
            summary += f"  New: {entry.new_value}\n"
            if entry.reason:
                summary += f"  Reason: {entry.reason}\n"
            summary += "\n"
        
        return summary
