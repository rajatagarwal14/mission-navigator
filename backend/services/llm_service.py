import asyncio
from typing import AsyncGenerator, Optional

import google.generativeai as genai

from config import settings
from data.system_prompts import CHAT_SYSTEM_PROMPT, CHAT_CRISIS_AUGMENTED_PROMPT


class LLMService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-2.5-flash"

    def _build_contents(
        self,
        user_message: str,
        context: str,
        conversation_history: list[dict] = None,
    ) -> list[dict]:
        """Build the conversation contents (history + current message with context)."""
        contents = []

        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-6:]:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [msg["content"]]})

        # Add current user message with knowledge base context
        if context and context != "No relevant information found in the knowledge base.":
            user_turn = f"Relevant resources from our knowledge base:\n{context}\n\nUser question: {user_message}"
        else:
            user_turn = user_message

        contents.append({"role": "user", "parts": [user_turn]})
        return contents

    def _get_model(self, crisis_tier: Optional[int] = None) -> genai.GenerativeModel:
        """Create a GenerativeModel with proper system instruction."""
        system = CHAT_SYSTEM_PROMPT
        if crisis_tier == 2:
            system += "\n\n" + CHAT_CRISIS_AUGMENTED_PROMPT

        return genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1024,
                top_p=0.8,
            ),
        )

    SAFETY_SETTINGS = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    async def generate(
        self,
        user_message: str,
        context: str,
        conversation_history: list[dict] = None,
        crisis_tier: Optional[int] = None,
    ) -> str:
        """Generate a complete response (non-streaming)."""
        model = self._get_model(crisis_tier)
        contents = self._build_contents(user_message, context, conversation_history)

        response = await asyncio.to_thread(
            model.generate_content,
            contents,
            safety_settings=self.SAFETY_SETTINGS,
        )

        return response.text

    async def generate_stream(
        self,
        user_message: str,
        context: str,
        conversation_history: list[dict] = None,
        crisis_tier: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response."""
        model = self._get_model(crisis_tier)
        contents = self._build_contents(user_message, context, conversation_history)

        def _generate():
            """Run blocking Gemini stream and collect all chunks."""
            stream = model.generate_content(
                contents,
                stream=True,
                safety_settings=self.SAFETY_SETTINGS,
            )
            chunks = []
            for chunk in stream:
                if chunk.text:
                    chunks.append(chunk.text)
            return chunks

        chunks = await asyncio.to_thread(_generate)
        for chunk in chunks:
            yield chunk


llm_service = LLMService()
