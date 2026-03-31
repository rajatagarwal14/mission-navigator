import json
import re
import os
from typing import Optional, Tuple

from data.system_prompts import CRISIS_IMMEDIATE_RESPONSE


class SafetyService:
    def __init__(self):
        self._load_crisis_keywords()
        self._compile_medical_patterns()

    def _load_crisis_keywords(self):
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "crisis_keywords.json")
        with open(data_path) as f:
            data = json.load(f)

        self.tier1_patterns = [p.lower() for p in data["tier1_immediate"]["patterns"]]
        self.tier2_patterns = [p.lower() for p in data["tier2_elevated"]["patterns"]]
        self.tier3_patterns = [p.lower() for p in data["tier3_contextual"]["patterns"]]

    def _compile_medical_patterns(self):
        medical_phrases = [
            r"you should take\b",
            r"i recommend (that you |)(taking|starting|trying)",
            r"your diagnosis (is|might be|could be)",
            r"you (likely |probably |)have \w+ disorder",
            r"(increase|decrease|change|stop) your (medication|dosage|prescription)",
            r"you (need|should) (see|visit) a (doctor|psychiatrist|physician)",
            r"based on (your|these) symptoms.{0,20}(you have|this is|diagnosis)",
            r"prescri(be|ption)",
            r"(take|try) (some |)\d+ ?mg",
        ]
        self.medical_regex = re.compile("|".join(medical_phrases), re.IGNORECASE)

    def check_crisis(self, message: str) -> Tuple[Optional[int], Optional[str]]:
        """Check message for crisis indicators. Returns (tier, response) or (None, None)."""
        text = message.lower().strip()

        # Tier 1: Immediate crisis - bypass LLM entirely
        for pattern in self.tier1_patterns:
            if pattern in text:
                return 1, CRISIS_IMMEDIATE_RESPONSE

        # Tier 2: Elevated concern - augment LLM prompt
        for pattern in self.tier2_patterns:
            if pattern in text:
                return 2, None

        # Tier 3: Contextual - flag for analytics
        for pattern in self.tier3_patterns:
            if pattern in text:
                return 3, None

        return None, None

    def validate_response(self, response: str, context_phones: list[str] = None, context_urls: list[str] = None) -> Tuple[bool, Optional[str]]:
        """Validate LLM output for safety. Returns (is_valid, reason)."""
        # Check for medical advice
        if self.medical_regex.search(response):
            return False, "Response contains potential medical advice"

        # Check for phone numbers not in context
        if context_phones:
            phone_pattern = re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b")
            found_phones = phone_pattern.findall(response)
            allowed = set()
            for p in context_phones:
                digits = re.sub(r"\D", "", p)
                allowed.add(digits)
            # Always allow known crisis lines
            allowed.update({"988", "8382559", "8003429647", "3129428387"})
            for phone in found_phones:
                digits = re.sub(r"\D", "", phone)
                if digits not in allowed and not any(digits in a for a in allowed):
                    return False, f"Response contains unverified phone number: {phone}"

        return True, None

    def is_off_topic(self, message: str) -> bool:
        """Check if a message is clearly off-topic for the Road Home Program."""
        off_topic_patterns = [
            r"\b(stock|crypto|bitcoin|invest|trading)\b",
            r"\b(recipe|cook|food prep)\b",
            r"\b(sports score|game result|who won)\b",
            r"\b(write me a (poem|story|essay|song))\b",
            r"\b(what is the (weather|temperature))\b",
            r"\b(tell me a joke|funny story)\b",
        ]
        text = message.lower()
        for pattern in off_topic_patterns:
            if re.search(pattern, text):
                return True
        return False

    def get_off_topic_response(self) -> str:
        return (
            "I'm designed specifically to help you find mental health services and resources "
            "through the Road Home Program. I'm not able to help with that particular topic, "
            "but I'd love to help you explore the support services available to veterans and "
            "military families.\n\n"
            "Here are some things I can help with:\n"
            "- Finding mental health services for veterans and families\n"
            "- Learning about the Road Home Program's treatment options\n"
            "- Connecting you with financial, educational, or caregiver support\n"
            "- Understanding eligibility for different programs\n\n"
            "What would you like to know about?"
        )


# Singleton instance
safety_service = SafetyService()
