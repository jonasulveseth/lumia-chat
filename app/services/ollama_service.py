"""
Ollama service for LLM communication.
"""
import time
import httpx
import json
from typing import AsyncGenerator, Optional, List
from app.core.config import settings
from app.core.prompts import PromptTemplates, PromptInstructions


class OllamaService:
    """Service for communicating with Ollama LLM."""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.llm_model
        self.gatekeeper_model = getattr(settings, "gatekeeper_model", None)
        self._last_warmup_time = 0
        self._warmup_interval = 30  # Re-warm every 30 seconds to keep model hot
    
    async def _strip_think_stream_async(self, piece_iter):
        """Async generator that strips <think>...</think> sections from streamed text.
        Maintains state across chunks so tags split across boundaries are handled.
        """
        if not settings.strip_think_sections:
            async for piece in piece_iter:
                yield piece
            return
        inside = 0
        buffer = ""
        async for piece in piece_iter:
            buffer += piece
            out_chars = []
            i = 0
            while i < len(buffer):
                if buffer.startswith("<think>", i):
                    inside += 1
                    i += len("<think>")
                    continue
                if buffer.startswith("</think>", i):
                    inside = max(inside - 1, 0)
                    i += len("</think>")
                    continue
                # If we are near a potential tag start at the very end, keep it in buffer
                # to be disambiguated by the next chunk
                remaining = len(buffer) - i
                if remaining <= 7:  # len("</think") == 7
                    break
                if inside == 0:
                    out_chars.append(buffer[i])
                i += 1
            # Emit what we confidently processed
            emitted = "".join(out_chars)
            if emitted:
                yield emitted
            # Keep tail for next iteration
            buffer = buffer[i:]
        # Flush any remaining safe text if not inside a tag
        if inside == 0 and buffer:
            # Remove any dangling partial tag text
            if buffer.endswith("<think") or buffer.endswith("</think"):
                buffer = buffer[:-6]
            if buffer:
                yield buffer
    
    async def generate_response(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Generate response from Ollama LLM.
        
        Args:
            prompt: The user's message
            context: Optional context from Brain
            system_prompt: Optional system prompt to control AI behavior
            stream: Whether to stream the response
            
        Yields:
            Response chunks as strings
        """
        start_time = time.time()
        
        print(f"📝 Starting prompt preparation...")
        prompt_start = time.time()
        
        # Prepare the full prompt with context if available (optimized)
        full_prompt = PromptTemplates.get_chat_prompt(prompt, context)
        
        # Add topic-specific instruction (minimal for speed)
        instruction = PromptInstructions.get_instruction_for_topic(prompt)
        full_prompt = PromptInstructions.enhance_prompt_with_instruction(full_prompt, instruction)
        
        prompt_time = time.time() - prompt_start
        print(f"⏱️  Prompt preparation took: {prompt_time:.3f}s")
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": stream,
            "keep_alive": "10m",  # Keep model loaded for fast subsequent requests
            "think": False,       # Disable thinking mode at top level (per Ollama docs)
            "options": {
                "temperature": 0.7,
                "max_tokens": 1024,   # Back to reasonable size
                "num_predict": 1024,  # Back to reasonable size  
                "num_ctx": 2048,      # Back to full context
                "num_thread": 8       # More threads for faster processing
            }
        }
        
        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt
            print(f"🎭 Using system prompt: {system_prompt[:50]}...")
        
        print(f"📤 Sending request to Ollama ({self.model})...")
        ollama_start = time.time()
        
        # Create client with optimized settings
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=60.0
                ) as response:
                    response.raise_for_status()
                    
                    first_chunk_time = None
                    chunk_count = 0
                    
                    async def raw_chunks():
                        nonlocal first_chunk_time
                        async for line in response.aiter_lines():
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    if "response" in data:
                                        if first_chunk_time is None:
                                            first_chunk_time = time.time() - ollama_start
                                            print(f"⏱️  First chunk received after: {first_chunk_time:.2f}s")
                                        yield data["response"]
                                    if data.get("done", False):
                                        break
                                except json.JSONDecodeError:
                                    continue
                    
                    async for cleaned in self._strip_think_stream_async(raw_chunks()):
                        chunk_count += 1
                        yield cleaned
                    
                    total_ollama_time = time.time() - ollama_start
                    print(f"⏱️  Ollama total generation time: {total_ollama_time:.2f}s")
                    print(f"📊 Generated {chunk_count} chunks (post-filter)")
            except httpx.HTTPError as e:
                yield f"Error communicating with Ollama: {str(e)}"
            except Exception as e:
                yield f"Unexpected error: {str(e)}"

    def gatekeeper_score(self, text: str) -> Optional[float]:
        """Fast heuristic to score whether text is worth prefetching context for.
        Returns a score in [0,1] based on length and content quality.
        Much faster than calling an LLM for each keystroke.
        """
        if not text or len(text.strip()) < 3:
            return 0.0
        
        text = text.strip().lower()
        length = len(text)
        
        # Base score from length (longer = more likely complete)
        if length < 5:
            base_score = 0.1
        elif length < 10:
            base_score = 0.3
        elif length < 20:
            base_score = 0.6
        else:
            base_score = 0.8
        
        # Boost for complete question patterns
        question_words = ["vad", "när", "hur", "varför", "vilken", "kan du", "vill du", "berätta", "?"]
        if any(word in text for word in question_words):
            base_score += 0.2
        
        # Boost for date/time references
        time_words = ["igår", "idag", "imorgon", "förra", "nästa", "augusti", "måndags", "tisdags"]
        if any(word in text for word in time_words):
            base_score += 0.2
        
        # Big boost for complete sentences (ends with punctuation)
        if text.endswith((".", "?", "!")):
            base_score += 0.3
        
        # Penalty for incomplete patterns
        incomplete_endings = [" ", "och", "eller", "men", "att", "som", "det", "jag", "för"]
        if any(text.endswith(ending) for ending in incomplete_endings):
            base_score -= 0.3
        
        # Penalty for very short fragments  
        if length < 8:
            base_score -= 0.2
        
        return max(0.0, min(1.0, base_score))

    async def needs_brain_context(self, message: str) -> bool:
        """
        Use a lightweight LLM to determine if a message needs Brain context.
        Returns True if Brain context is needed, False if it can be answered without context.
        """
        if not message or len(message.strip()) < 2:
            return False
            
        # Use qwen3:1.7b for fast decision making
        prompt = f"""Du ska avgöra om följande meddelande behöver information från en historisk databas eller kan besvaras direkt.

Meddelande: "{message}"

Svar NEJ endast för enkla frågor som:
- "Hej" (hälsning)
- "Tack" (bekräftelse)
- "Hur mår du?" (allmän fråga)
- "Vad heter du?" (allmän fråga)

Svar JA för frågor om:
- Åsikter och feedback: "vad tycker du om X?"
- Produkter och tjänster: "vad tycker du om produkten?"
- Specifika projekt som "bygger.ai" eller "reemove"
- Tidigare diskussioner: "vad pratade vi om igår?"
- Specifika namn eller företag som användaren pratat om
- Allmänna frågor som kan ha kontext: "vad tycker du?"
- Uppföljningsfrågor: "vilken plattform?", "vad menar du med X?"
- Frågor som refererar till tidigare konversation: "vad sa jag om X?"
- Frågor som behöver kontext för att förstå: "vad är det du pratar om?"

Exempel:
"Vad tycker du?" → JA (kan ha kontext)
"Vad tycker du om produkten?" → JA
"Vad vet du om bygger.ai?" → JA
"Vilken plattform?" → JA (uppföljningsfråga)
"Vad menar du med plattform?" → JA (uppföljningsfråga)
"Hej" → NEJ

Svara endast JA eller NEJ:"""

        try:
            payload = {
                "model": "qwen3:1.7b",  # Lightweight model for fast decisions
                "prompt": prompt,
                "stream": False,
                "keep_alive": "5m",
                "think": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent decisions
                    "max_tokens": 10,
                    "num_predict": 10,
                    "num_ctx": 1024,
                    "num_thread": 4
                }
            }
            
            timeout = httpx.Timeout(3.0, connect=1.0)  # Fast timeout
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
                
                result = data.get("response", "").strip().upper()
                needs_context = "JA" in result
                
                print(f"🤖 Brain decision: '{message[:30]}...' → {'NEEDS' if needs_context else 'SKIP'} ({result})")
                return needs_context
                
        except Exception as e:
            print(f"❌ Brain decision error: {e}, defaulting to NEEDS context")
            return True  # Default to using Brain if decision fails

    async def warmup_main_model(self, force: bool = False) -> None:
        """Prime the main model so first-token latency is lower.
        Uses smart caching to avoid redundant warmups.
        """
        current_time = time.time()
        
        # Skip if recently warmed up (unless forced)
        if not force and (current_time - self._last_warmup_time) < self._warmup_interval:
            return
            
        try:
            print(f"🔥 Warming up main model: {self.model}")
            warmup_start = time.time()
            
            payload = {
                "model": self.model,
                "prompt": "OK",
                "stream": False,
                "keep_alive": "10m",  # Keep model loaded for 10 minutes
                "think": False,       # Disable thinking for faster warmup
                "options": {
                    "temperature": 0.0, 
                    "num_predict": 1,
                    "num_ctx": 2048,  # Load with context size
                    "num_thread": 4
                }
            }
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=8.0)) as client:
                resp = await client.post(f"{self.base_url}/api/generate", json=payload, timeout=20.0)
                warmup_time = time.time() - warmup_start
                
                if resp.status_code == 200:
                    self._last_warmup_time = current_time
                    print(f"✅ Model {self.model} warmed up in {warmup_time:.2f}s")
                else:
                    print(f"⚠️ Model warmup returned status {resp.status_code}")
        except Exception as e:
            print(f"❌ Model warmup failed: {e}")

    def should_warmup(self) -> bool:
        """Check if model needs warming up."""
        return (time.time() - self._last_warmup_time) >= self._warmup_interval
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text using Ollama.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if error
        """
        payload = {
            "model": settings.embedding_model,
            "prompt": text
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("embedding")
                
            except Exception as e:
                print(f"Error generating embedding: {e}")
                return None
    
    async def list_models(self) -> List[str]:
        """
        List available Ollama models.
        
        Returns:
            List of model names
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
                
            except Exception as e:
                print(f"Error listing models: {e}")
                return [] 