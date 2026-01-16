"""
Multi-LLM Client for Kai - Economist
Provides automatic fallback from Gemini to Groq (Llama-3) on quota limits.
"""

import os
import time
import random
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class MultiLLMClient:
    """
    Unified LLM client with automatic fallback and retry logic.
    """
    
    def __init__(self, system_instruction: str, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize LLM clients.
        
        Args:
            system_instruction: System prompt for the agent
            model_name: Primary model name (Gemini)
        """
        self.system_instruction = system_instruction
        self.primary_model_name = model_name
        self.fallback_model_name = "llama-3.3-70b-versatile"
        
        # Initialize Gemini
        gemini_key = os.getenv("GOOGLE_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini_model = genai.GenerativeModel(
                model_name=self.primary_model_name,
                system_instruction=system_instruction
            )
        else:
            self.gemini_model = None
            
        # Initialize Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            self.groq_client = Groq(api_key=groq_key)
        else:
            self.groq_client = None
            
    def generate_content(self, prompt: str, max_retries: int = 3) -> Any:
        """
        Generate content with priority: Groq -> Gemini.
        """
        # 1. Try Groq first
        if self.groq_client:
            try:
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": self.system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    model=self.fallback_model_name, # Using what was "fallback" as primary now
                )
                
                # Wrap Groq response to look like Gemini response
                class GroqResponseWrapper:
                    def __init__(self, text, prompt_tokens, completion_tokens):
                        self.text = text
                        class UsageMetadata:
                            def __init__(self, pt, ct):
                                self.prompt_token_count = pt
                                self.candidates_token_count = ct
                                self.total_token_count = pt + ct
                        self.usage_metadata = UsageMetadata(prompt_tokens, completion_tokens)
                
                return GroqResponseWrapper(
                    chat_completion.choices[0].message.content,
                    chat_completion.usage.prompt_tokens,
                    chat_completion.usage.completion_tokens
                )
            except Exception as e:
                print(f"[LLM] Groq call failed: {e}. Falling back to Gemini...")
                # Proceed to Gemini fallback
        
        # 2. Fallback to Gemini
        if self.gemini_model:
            for attempt in range(max_retries):
                try:
                    return self.gemini_model.generate_content(prompt)
                except Exception as e:
                    if "429" in str(e):
                        if attempt < max_retries - 1:
                            delay = 5 * (2 ** attempt) + random.uniform(0, 1)
                            print(f"[LLM] Gemini quota exceeded. Retrying in {delay:.2f}s...")
                            time.sleep(delay)
                            continue
                        else:
                            print(f"[LLM] Gemini quota exhausted and Groq failed/unavailable.")
                            raise e 
                    else:
                        raise e
            return # Should be unreachable if max_retries > 0 loop logic holds or raises
        else:
            raise ValueError("No LLM clients available or both failed.")
