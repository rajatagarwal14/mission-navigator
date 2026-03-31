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

    def _build_prompt(
        self,
        user_message: str,
        context: str,
        conversation_history: list[dict] = None,
        crisis_tier: Optional[int] = None,
    ) -> list[dict]:
        """Build the full prompt for Gemini."""
        system = CHAT_SYSTEM_PROMPT
        if crisis_tier == 2:
            system += "\n\n" + CHAT_CRISIS_AUGMENTED_PROMPT

        contents = []

        # Add system instruction as first user message context
        system_context = f"{system}\n\n---\nKNOWLEDGE BASE CONTEXT:\n{context}\n---"

        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 6 messages
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [msg["content"]]})

        # Add current message with context
        if not contents:
            contents.append({"role": "user", "parts": [f"{system_context}\n\nUser question: {user_message}"]})
        else:
            contents.append({"role": "user", "parts": [f"Context:\n{context}\n\nUser question: {user_message}"]})

        return contents, system_context

    async def generate(
        self,
        user_message: str,
        context: str,
        conversation_history: list[dict] = None,
        crisis_tier: Optional[int] = None,
    ) -> str:
        """Generate a complete response (non-streaming)."""
        model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1024,
                top_p=0.8,
            ),
        )

        contents, system_context = self._build_prompt(
            user_message, context, conversation_history, crisis_tier
        )

        response = await asyncio.to_thread(
            model.generate_content,
            contents,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ],
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
        model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1024,
                top_p=0.8,
            ),
        )

        contents, system_context = self._build_prompt(
            user_message, context, conversation_history, crisis_tier
        )

        def _generate():
            """Run blocking Gemini stream and collect all chunks."""
            stream = model.generate_content(
                contents,
                stream=True,
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ],
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
