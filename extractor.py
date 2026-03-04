"""
Extraction engine: Parse transcripts and extract structured account memo.
Rule-based extraction (zero LLM cost).
"""

import re
from typing import Dict, List, Optional, Tuple
from schemas import AccountMemo, BusinessHours, RoutingRule


class TranscriptExtractor:
    """
    Rule-based extractor for demo and onboarding call transcripts.
    Never hallucinate. Flag unknowns explicitly.
    """
    
    def __init__(self):
        self.unknowns = []
    
    def extract_account_memo(self, 
                            transcript: str, 
                            call_type: str = "demo",
                            account_id: Optional[str] = None) -> AccountMemo:
        """
        Extract structured account memo from transcript.
        call_type: "demo" or "onboarding"
        """
        self.unknowns = []
        
        # Extract each field systematically
        company_name = self._extract_company_name(transcript)
        industry = self._extract_industry(transcript)
        office_address = self._extract_address(transcript)
        office_phone = self._extract_phone(transcript)
        services = self._extract_services(transcript)
        emergency_triggers = self._extract_emergency_definition(transcript)
        business_hours = self._extract_business_hours(transcript)
        emergency_routing = self._extract_emergency_routing(transcript)
        non_emergency_routing = self._extract_non_emergency_routing(transcript)
        transfer_timeout = self._extract_transfer_timeout(transcript)
        integration_constraints = self._extract_integration_constraints(transcript)
        after_hours_summary = self._extract_after_hours_summary(transcript)
        office_hours_summary = self._extract_office_hours_summary(transcript)
        notes = self._extract_notes(transcript)
        
        # Generate account_id if not provided
        if not account_id:
            account_id = f"acc_{company_name.lower().replace(' ', '_')[:20]}"
        
        memo = AccountMemo(
            account_id=account_id,
            company_name=company_name or "UNKNOWN",
            industry=industry,
            business_hours=business_hours,
            office_address=office_address,
            office_phone=office_phone,
            services_supported=services,
            emergency_definition=emergency_triggers,
            emergency_routing_rules=emergency_routing,
            non_emergency_routing_rules=non_emergency_routing,
            call_transfer_timeout_seconds=transfer_timeout,
            integration_constraints=integration_constraints,
            after_hours_flow_summary=after_hours_summary,
            office_hours_flow_summary=office_hours_summary,
            questions_or_unknowns=self.unknowns,
            notes=notes,
        )
        
        return memo
    
    def _extract_company_name(self, transcript: str) -> Optional[str]:
        """Extract company name from transcript."""
        # Look for patterns like "Company: X" or "This is X calling"
        patterns = [
            r"(?:company|company name|working with|this is|for)\s+([A-Z][A-Za-z\s&'.-]{2,40}?)(?:\s+(?:here|calling|is a|services|company|inc|ltd|llc|corp)|\.|,|$)",
            r"([A-Z][A-Za-z\s&'.-]{2,40}?)\s+(?:fire protection|sprinkler|hvac|electrical|alarm|services)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out common words that aren't part of company name
                if name.lower() not in ['the', 'a', 'an', 'is', 'are', 'do', 'does']:
                    return name
        
        self.unknowns.append("company_name: not explicitly stated in transcript")
        return None
    
    def _extract_industry(self, transcript: str) -> Optional[str]:
        """Extract industry/service type."""
        industries = {
            r"fire\s+protection|fire\s+safety": "Fire Protection",
            r"sprinkler": "Sprinkler Systems",
            r"alarm.*monitoring|monitoring.*alarm": "Alarm Monitoring",
            r"hvac|heating|cooling|air\s+conditioning": "HVAC",
            r"electrical|electric": "Electrical Services",
            r"plumbing": "Plumbing",
            r"maintenance|facilities": "Facilities Maintenance",
        }
        
        for pattern, industry_name in industries.items():
            if re.search(pattern, transcript, re.IGNORECASE):
                return industry_name
        
        self.unknowns.append("industry: service type not explicitly mentioned")
        return None
    
    def _extract_address(self, transcript: str) -> Optional[str]:
        """Extract office address."""
        # Look for address patterns with street, city, state
        patterns = [
                r"(?:address|located at|office address|office at)\s*:?\s*"
                r"(\d+\s+[A-Za-z0-9\s.,#-]+?"
                r"(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|boulevard|blvd|way|circle|court|ct)"
                r"[A-Za-z0-9\s.,#-]*?,\s*"
                r"[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?)"
      ]
        
        for pattern in patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        self.unknowns.append("office_address: specific address not provided in transcript")
        return None
    
    def _extract_phone(self, transcript: str) -> Optional[str]:
        """Extract office phone number."""
        patterns = [
            r"(?:phone|number|reach|call us at)\s*:?\s*(\(?[\d\s\-\.]{10,14}\)?)",
            r"(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, transcript)
            if match:
                phone = match.group(1)
                # Basic validation
                if len(re.sub(r"\D", "", phone)) >= 10:
                    return phone.strip()
        
        self.unknowns.append("office_phone: phone number not provided")
        return None
    
    def _extract_services(self, transcript: str) -> List[str]:
        """Extract list of services offered."""
        services_map = {
            r"sprinkler": "Sprinkler Service",
            r"fire alarm|alarm": "Alarm Response",
            r"extinguisher": "Extinguisher Service",
            r"hvac|heating|cooling": "HVAC Service",
            r"electrical": "Electrical Service",
            r"plumbing": "Plumbing Service",
            r"inspection": "Inspection",
            r"maintenance": "Maintenance",
            r"emergency": "Emergency Response",
        }
        
        services = []
        for pattern, service_name in services_map.items():
            if re.search(pattern, transcript, re.IGNORECASE):
                if service_name not in services:
                    services.append(service_name)
        
        if not services:
            self.unknowns.append("services_supported: no specific services mentioned")
        
        return services
    
    def _extract_emergency_definition(self, transcript: str) -> List[str]:
        """Extract what counts as emergency."""
        emergency_triggers = []
        
        triggers_map = {
            r"sprinkler.*(leak|break|burst|off)": "Sprinkler leak/burst",
            r"fire.*(alarm|triggered|activated)": "Fire alarm activation",
            r"alarm.*trigger|triggered.*alarm": "Alarm triggered",
            r"no water|water.*(off|loss)": "Loss of water pressure",
            r"system.*offline|not responding": "Sprinkler system not responding",
            r"hazard|immediate.*danger|life.*safety": "Immediate safety hazard",
        }
        
        for pattern, trigger in triggers_map.items():
            if re.search(pattern, transcript, re.IGNORECASE):
                if trigger not in emergency_triggers:
                    emergency_triggers.append(trigger)
        
        if not emergency_triggers:
            self.unknowns.append("emergency_definition: emergency triggers not clearly defined")
        
        return emergency_triggers
    
    # def _extract_business_hours(self, transcript: str) -> BusinessHours:
    #     """Extract business hours."""
    #     hours = BusinessHours()
        
    #     # Look for timezone
    #     tz_patterns = {
    #         r"eastern|est|et": "EST",
    #         r"central|cst|ct": "CST",
    #         r"mountain|mst|mt": "MST",
    #         r"pacific|pst|pt": "PST",
    #         r"utc|gmt": "UTC",
    #     }
        
    #     for pattern, tz in tz_patterns.items():
    #         if re.search(pattern, transcript, re.IGNORECASE):
    #             hours.timezone = tz
    #             break
        
    #     # Look for specific business hour mentions
    #     time_pattern = r"(\d{1,2}):?(\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)"
    #     times = re.findall(time_pattern, transcript, re.IGNORECASE)
        
    #     if times:
    #         # Simple heuristic: assume first time is start, second is end
    #         for t in times[:2]:
    #             pass  # Would need more sophisticated parsing for different days
            
    #         self.unknowns.append("business_hours: needs detailed onboarding for exact times per day")
    #     else:
    #         self.unknowns.append("business_hours: no specific business hours mentioned")
        
    #     return hours

    def _extract_business_hours(self, transcript: str) -> BusinessHours:
        """Extract business hours including days and exact times."""
        hours = BusinessHours()

        # Timezone detection
        tz_patterns = {
            r"eastern|est|et": "EST",
            r"central|cst|ct": "CST",
            r"mountain|mst|mt": "MST",
            r"pacific|pst|pt": "PST",
            r"utc|gmt": "UTC",
        }

        for pattern, tz in tz_patterns.items():
            if re.search(pattern, transcript, re.IGNORECASE):
                hours.timezone = tz
                break

        # Detect Mon-Fri 8 AM - 5 PM pattern
        match = re.search(
            r"(mon(?:day)?-?fri(?:day)?).*?(\d{1,2})\s*(am|pm).*?(\d{1,2})\s*(am|pm)",
            transcript,
            re.IGNORECASE
        )

        if match:
            start_hour = int(match.group(2))
            start_ampm = match.group(3).lower()
            end_hour = int(match.group(4))
            end_ampm = match.group(5).lower()

            if start_ampm == "pm" and start_hour != 12:
                start_hour += 12
            if end_ampm == "pm" and end_hour != 12:
                end_hour += 12

            start = f"{start_hour:02d}:00"
            end = f"{end_hour:02d}:00"

            for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                setattr(hours, f"{day}_start", start)
                setattr(hours, f"{day}_end", end)

        else:
            self.unknowns.append("business_hours: no specific business hours mentioned")

        return hours
    
    # def _extract_emergency_routing(self, transcript: str) -> List[RoutingRule]:
    #     """Extract emergency routing rules."""
    #     rules = []
    #     order = 1
        
    #     # Look for routing mentions
    #     if re.search(r"emergency.*dispatch|dispatch.*emergency", transcript, re.IGNORECASE):
    #         rules.append(RoutingRule(
    #             order=order,
    #             target_type="dispatch",
    #             target_value="on-site dispatch center",
    #             description="Emergency dispatch team"
    #         ))
    #         order += 1
        
    #     if re.search(r"emergency.*operator|operator.*phone|phone.*operator", transcript, re.IGNORECASE):
    #         phone_match = re.search(r"\(?[\d\s\-\.]{10,14}\)?", transcript)
    #         if phone_match:
    #             rules.append(RoutingRule(
    #                 order=order,
    #                 target_type="phone",
    #                 target_value=phone_match.group(0),
    #                 description="Emergency operator"
    #             ))
        
    #     if not rules:
    #         self.unknowns.append("emergency_routing: specific emergency routing rules not defined")
        
    #     return rules


    def _extract_emergency_routing(self, transcript: str) -> List[RoutingRule]:
        rules = []
        order = 1

        # Extract dispatch phone (e.g., 555-2847)
        phone_match = re.search(r"\b\d{3}-\d{4}\b", transcript)

        if phone_match:
            rules.append(RoutingRule(
                order=order,
                target_type="phone",
                target_value=phone_match.group(0),
                description="Emergency dispatch line"
            ))
            order += 1

        elif re.search(r"dispatch", transcript, re.IGNORECASE):
            rules.append(RoutingRule(
                order=order,
                target_type="dispatch",
                target_value="on-site dispatch center",
                description="Emergency dispatch team"
            ))

        if not rules:
            self.unknowns.append("emergency_routing: specific emergency routing rules not defined")

        return rules
    
    # def _extract_non_emergency_routing(self, transcript: str) -> List[RoutingRule]:
    #     """Extract non-emergency routing rules."""
    #     rules = []
        
    #     # Look for non-emergency routing
    #     if re.search(r"after.*hours.*collect|collect.*details|voicemail|message", transcript, re.IGNORECASE):
    #         rules.append(RoutingRule(
    #             order=1,
    #             target_type="voicemail",
    #             target_value="voicemail system",
    #             description="After hours: collect details in voicemail"
    #         ))
        
    #     if not rules:
    #         self.unknowns.append("non_emergency_routing: non-emergency routing not specified")
        
    #     return rules

    def _extract_non_emergency_routing(self, transcript: str) -> List[RoutingRule]:
        rules = []
        order = 1

        # After-hours voicemail
        if re.search(r"after.*hours.*collect|voicemail|message", transcript, re.IGNORECASE):
            rules.append(RoutingRule(
                order=order,
                target_type="voicemail",
                target_value="voicemail system",
                description="After hours: collect details in voicemail"
            ))
            order += 1

        # Business-hours receptionist extension
        ext_match = re.search(r"ext\.?\s*(\d+)", transcript, re.IGNORECASE)
        if ext_match:
            rules.append(RoutingRule(
                order=order,
                target_type="extension",
                target_value=ext_match.group(1),
                description="Receptionist during business hours"
            ))

        if not rules:
            self.unknowns.append("non_emergency_routing: non-emergency routing not specified")

        return rules
    
    def _extract_transfer_timeout(self, transcript: str) -> Optional[int]:
        """Extract transfer timeout in seconds."""
        patterns = [
            r"(?:timeout|wait|try for|attempt for)\s+(\d+)\s*(?:second|sec|s)(?!ervice)",
            r"(\d+)\s*(?:second|sec)\s+timeout",
            r"(\d+)[-\s]*second",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        self.unknowns.append("call_transfer_timeout: not specified, recommend 30-60 seconds")
        return None
    
    def _extract_integration_constraints(self, transcript: str) -> List[str]:
        """Extract integration constraints (e.g., ServiceTrade rules)."""
        constraints = []
        
        constraint_patterns = {
            r"(?:never|don't|do not|avoid).*servicetrade.*sprinkler": "Never create sprinkler jobs in ServiceTrade",
            r"(?:never|don't|do not).*create.*job": "Avoid auto-creating service jobs",
            r"(?:only|must).*manual.*creation|manual.*entry": "Requires manual job creation",
        }
        
        for pattern, constraint in constraint_patterns.items():
            if re.search(pattern, transcript, re.IGNORECASE):
                if constraint not in constraints:
                    constraints.append(constraint)
        
        return constraints
    
    def _extract_after_hours_summary(self, transcript: str) -> Optional[str]:
        """Extract summary of after-hours handling."""
        if re.search(r"after.*hours|overnight|night|outside.*hours", transcript, re.IGNORECASE):
            # Create summary from context
            if re.search(r"emergency", transcript, re.IGNORECASE):
                return "After hours: Emergency calls routed to dispatch/operator; non-emergency details collected via voicemail"
        
        self.unknowns.append("after_hours_flow: after-hours procedures not discussed")
        return None
    
    def _extract_office_hours_summary(self, transcript: str) -> Optional[str]:
        """Extract summary of office hours handling."""
        if re.search(r"office.*hours|business.*hours|during.*hours|open", transcript, re.IGNORECASE):
            return "Office hours: Calls transferred to appropriate department or operator"
        
        self.unknowns.append("office_hours_flow: office hours procedures not clearly defined")
        return None
    
    def _extract_notes(self, transcript: str) -> Optional[str]:
        """Extract any additional notes."""
        # Look for special considerations
        if re.search(r"important|note|consider|special|requirement|constraint", transcript, re.IGNORECASE):
            return "Special considerations discussed during call - see questions_or_unknowns for details"
        
        return None
