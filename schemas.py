"""
Core data schemas for Clara Automation Pipeline.
Defines account memo structure, agent spec, and changelog format.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


@dataclass
class BusinessHours:
    """Represents business hours configuration."""
    monday_start: Optional[str] = None  # "09:00"
    monday_end: Optional[str] = None    # "17:00"
    tuesday_start: Optional[str] = None
    tuesday_end: Optional[str] = None
    wednesday_start: Optional[str] = None
    wednesday_end: Optional[str] = None
    thursday_start: Optional[str] = None
    thursday_end: Optional[str] = None
    friday_start: Optional[str] = None
    friday_end: Optional[str] = None
    saturday_start: Optional[str] = None
    saturday_end: Optional[str] = None
    sunday_start: Optional[str] = None
    sunday_end: Optional[str] = None
    timezone: Optional[str] = None  # "EST", "PST", etc.


@dataclass
class RoutingRule:
    """Single routing target."""
    order: int
    target_type: str  # "phone", "email", "dispatch"
    target_value: str
    description: Optional[str] = None


@dataclass
class AccountMemo:
    """Structured account configuration extracted from demo or onboarding."""
    account_id: str
    company_name: str
    industry: Optional[str] = None  # "Fire Protection", "HVAC", etc.
    business_hours: Optional[BusinessHours] = field(default_factory=BusinessHours)
    office_address: Optional[str] = None
    office_phone: Optional[str] = None
    services_supported: List[str] = field(default_factory=list)  # ["sprinkler", "fire alarm"]
    emergency_definition: List[str] = field(default_factory=list)  # Triggers
    emergency_routing_rules: List[RoutingRule] = field(default_factory=list)
    non_emergency_routing_rules: List[RoutingRule] = field(default_factory=list)
    call_transfer_timeout_seconds: Optional[int] = None
    call_transfer_retries: Optional[int] = None
    integration_constraints: List[str] = field(default_factory=list)  # "never create sprinkler jobs"
    after_hours_flow_summary: Optional[str] = None
    office_hours_flow_summary: Optional[str] = None
    questions_or_unknowns: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> "AccountMemo":
        """Reconstruct AccountMemo from dict, handling nested objects."""
        # Handle BusinessHours
        if isinstance(data.get("business_hours"), dict):
            data["business_hours"] = BusinessHours(**data["business_hours"])
        elif data.get("business_hours") is None:
            data["business_hours"] = BusinessHours()
        
        # Handle routing rules
        if data.get("emergency_routing_rules"):
            data["emergency_routing_rules"] = [
                RoutingRule(**r) if isinstance(r, dict) else r
                for r in data["emergency_routing_rules"]
            ]
        
        if data.get("non_emergency_routing_rules"):
            data["non_emergency_routing_rules"] = [
                RoutingRule(**r) if isinstance(r, dict) else r
                for r in data["non_emergency_routing_rules"]
            ]
        
        return AccountMemo(**data)


@dataclass
class RetellAgentSpec:
    """Retell agent configuration spec."""
    agent_id: Optional[str] = None  # Assigned when created in Retell
    agent_name: str = ""
    version: str = "v1"  # "v1" from demo, "v2" from onboarding
    account_id: str = ""
    voice_style: str = "professional"  # "professional", "friendly", etc.
    system_prompt: str = ""
    key_variables: Dict[str, Any] = field(default_factory=dict)
    call_transfer_protocol: str = ""
    fallback_protocol: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> "RetellAgentSpec":
        return RetellAgentSpec(**data)


@dataclass
class ChangelogEntry:
    """Single changelog entry for a field change."""
    field_name: str
    old_value: Any
    new_value: Any
    source: str  # "demo", "onboarding"
    reason: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Changelog:
    """Full changelog for an account version transition."""
    account_id: str
    from_version: str  # "v1"
    to_version: str    # "v2"
    entries: List[ChangelogEntry] = field(default_factory=list)
    summary: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self):
        return {
            "account_id": self.account_id,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "entries": [asdict(e) for e in self.entries],
            "summary": self.summary,
            "created_at": self.created_at,
        }
    
    def add_change(self, field: str, old_val: Any, new_val: Any, source: str, reason: str = None):
        """Add a single change entry."""
        if old_val != new_val:
            self.entries.append(ChangelogEntry(
                field_name=field,
                old_value=old_val,
                new_value=new_val,
                source=source,
                reason=reason
            ))
