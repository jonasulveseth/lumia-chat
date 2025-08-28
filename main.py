"""
Lumia - Lokal AI-chattjänst med personligt minne

Huvudapplikation som kombinerar Ollama LLM med Brain RAG-tjänst.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from app.core.config import settings
from app.services.ollama_service import OllamaService
from app.api.chat import router as chat_router
from app.api.memory_chat import router as memory_router
from app.api.router_api import router as router_router
from app.api.threads import router as thread_router

# Skapa FastAPI-applikation
app = FastAPI(
    title="Lumia",
    description="Lokal AI-chattjänst med personligt minne",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # I produktion, specificera domäner
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inkludera routers
app.include_router(chat_router)
app.include_router(memory_router)
app.include_router(router_router)
app.include_router(thread_router)


# Warmup services function
async def warmup_services():
    """Warm up both Ollama and Brain services."""
    try:
        print("🔥 Starting service warmup...")
        
        # Warm up Ollama
        svc = OllamaService()
        await svc.warmup_main_model()
        
        # Warm up Brain API with a quick query
        import time
        from app.services.brain_service import BrainService
        brain = BrainService()
        print("🧠 Warming up Brain API...")
        start_time = time.time()
        await brain.query_quick_context(
            customer_id="warmup", 
            question="warmup", 
            n_results=1
        )
        warmup_time = time.time() - start_time
        print(f"✅ Brain API warmed up in {warmup_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Service warmup failed: {e}")

# Background task to keep Brain warm
async def keep_brain_warm():
    """Keep Brain API warm with periodic queries."""
    import asyncio
    from app.services.brain_service import BrainService
    
    brain = BrainService()
    while True:
        try:
            await asyncio.sleep(60)  # Wait 1 minute
            await brain.query_quick_context(
                customer_id="keepwarm", 
                question="keepwarm", 
                n_results=1
            )
            print("🔥 Brain keep-warm ping sent")
        except Exception as e:
            print(f"❌ Brain keep-warm failed: {e}")

# Use startup event with explicit call
@app.on_event("startup")
async def startup_event():
    print("🚀 Startup event triggered!")
    try:
        await warmup_services()
        print("✅ Startup warmup completed successfully!")
        
        # Start background Brain keep-warm task
        import asyncio
        asyncio.create_task(keep_brain_warm())
        print("🔥 Brain keep-warm task started")
        
    except Exception as e:
        print(f"❌ Startup warmup failed: {e}")
        import traceback
        traceback.print_exc()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Hemsida med enkel chat-interface."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lumia - AI Chat</title>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism.min.css">
        <script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/components/prism-core.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .chat-container {
                background: white;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .chat-messages {
                height: 500px;
                overflow-y: auto;
                border: 1px solid #ddd;
                padding: 10px;
                margin-bottom: 20px;
                border-radius: 5px;
                word-wrap: break-word;
                white-space: pre-wrap;
            }
            .message {
                margin-bottom: 10px;
                padding: 10px;
                border-radius: 5px;
            }
            .user-message {
                background: #e3f2fd;
                text-align: right;
            }
            .ai-message {
                background: #f5f5f5;
            }
            .ai-message h1, .ai-message h2, .ai-message h3, .ai-message h4, .ai-message h5, .ai-message h6 {
                margin: 10px 0 5px 0;
                color: #333;
            }
            .ai-message p {
                margin: 5px 0;
                line-height: 1.4;
            }
            .ai-message code {
                background: #f0f0f0;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
            .ai-message pre {
                background: #f8f8f8;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                margin: 10px 0;
            }
            .ai-message pre code {
                background: none;
                padding: 0;
            }
            .ai-message ul, .ai-message ol {
                margin: 5px 0;
                padding-left: 20px;
            }
            .ai-message blockquote {
                border-left: 4px solid #ddd;
                margin: 10px 0;
                padding-left: 10px;
                color: #666;
            }
            .ai-message strong {
                font-weight: bold;
            }
            .ai-message em {
                font-style: italic;
            }
            .input-container {
                display: flex;
                gap: 10px;
            }
            input[type="text"] {
                flex: 1;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            button {
                padding: 10px 20px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            button:hover {
                background: #5a6fd8;
            }
            .user-id {
                margin-bottom: 10px;
            }
            .user-id input {
                width: 200px;
            }
            .history-search {
                margin-bottom: 10px;
            }
            .history-search input {
                width: 150px;
            }
            .persona-section {
                margin-bottom: 10px;
            }
            .persona-section textarea {
                width: 100%;
                height: 100px;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-family: monospace;
                font-size: 12px;
                resize: vertical;
                background-color: #f9f9f9;
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <h1>🧠 Lumia - AI Chat</h1>
            <p>Din lokala AI-assistent med personligt minne</p>
            
            <div class="user-id">
                <label for="userId">Användar-ID:</label>
                <input type="text" id="userId" value="lumia_100023" placeholder="Ange användar-ID">
            </div>
            
            <div class="history-search">
                <label for="dateSearch">Sök historik (YYYY-MM-DD):</label>
                <input type="date" id="dateSearch" placeholder="2024-01-15">
                <button onclick="searchHistory()" style="margin-left: 10px;">Sök</button>
            </div>
            
            <div class="persona-section">
                <label for="personaDisplay">Personlighet (test):</label>
                <textarea id="personaDisplay" readonly placeholder="Klicka 'Visa personlighet' för att se..."></textarea>
                <button onclick="showPersona()" style="margin-left: 10px;">Visa personlighet</button>
                <button onclick="refreshPersona()" style="margin-left: 5px;">Uppdatera</button>
            </div>
            
            <div class="chat-messages" id="chatMessages">
                <div class="message ai-message">
                    <strong>Lumia:</strong> Hej! Jag är Lumia, din lokala AI-assistent. Hur kan jag hjälpa dig idag?
                </div>
            </div>
            
            <div class="input-container">
                <input type="text" id="messageInput" placeholder="Skriv ditt meddelande här..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">Skicka</button>
            </div>
        </div>

        <script>
            // Konfigurera Marked för bättre rendering
            marked.setOptions({
                breaks: true,
                gfm: true,
                sanitize: false
            });
            

            
            async function sendMessage() {
                const messageInput = document.getElementById('messageInput');
                const userIdInput = document.getElementById('userId');
                const chatMessages = document.getElementById('chatMessages');
                
                const message = messageInput.value.trim();
                const userId = userIdInput.value.trim();
                
                if (!message || !userId) return;
                
                // Lägg till användarens meddelande med timestamp
                const now = new Date();
                const timestamp = now.toLocaleString('sv-SE');
                const userDiv = document.createElement('div');
                userDiv.className = 'message user-message';
                userDiv.innerHTML = `<strong>Du:</strong> ${message}<br><small style="color: #666;">${timestamp}</small>`;
                chatMessages.appendChild(userDiv);
                
                // Lägg till AI-meddelande placeholder
                const aiDiv = document.createElement('div');
                aiDiv.className = 'message ai-message';
                const responseId = 'aiResponse_' + Date.now();
                aiDiv.innerHTML = `<strong>Lumia:</strong> <span id="${responseId}">Tänker...</span>`;
                chatMessages.appendChild(aiDiv);
                
                // Add loading indicator
                const loadingStart = Date.now();
                console.log('🚀 Starting request at:', new Date().toLocaleTimeString());
                
                // Rensa input
                messageInput.value = '';
                
                // Scrolla till botten
                chatMessages.scrollTop = chatMessages.scrollHeight;
                
                try {
                    console.log('🚀 Sending request to /memory/chat/stream...');
                    const response = await fetch('/memory/chat/stream', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            message: message,
                            user_id: userId
                        })
                    });
                    
                    console.log('📡 Response received, status:', response.status);
                    console.log('📡 Response headers:', response.headers);
                    
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    let aiResponse = '';
                    let chunkCount = 0;
                    
                    console.log('🔄 Starting to read chunks...');
                    
                    let streamDone = false;
                    while (!streamDone) {
                        const { done, value } = await reader.read();
                        if (done) {
                            console.log('✅ Stream completed');
                            break;
                        }
                        
                        const chunk = decoder.decode(value);
                        console.log('📦 Raw chunk received:', chunk.length, 'bytes');
                        
                        const lines = chunk.split('\\n');
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));
                                    // Debug prefetch disabled
                                    if (data.chunk) {
                                        chunkCount++;
                                        aiResponse += data.chunk;
                                        
                                        // Log first chunk timing
                                        if (chunkCount === 1) {
                                            const firstChunkTime = Date.now() - loadingStart;
                                            console.log('⚡ First chunk received after:', firstChunkTime + 'ms');
                                        }
                                        
                                        // Always render Markdown for proper formatting
                                        const htmlContent = marked.parse(aiResponse);
                                        document.getElementById(responseId).innerHTML = htmlContent;
                                        
                                        // Highlight syntax för kod
                                        Prism.highlightAllUnder(document.getElementById(responseId));
                                        
                                        // Ensure we scroll to the very bottom to see the latest content
                                        setTimeout(() => {
                                            chatMessages.scrollTop = chatMessages.scrollHeight;
                                        }, 100);
                                    }
                                    if (data.done) {
                                        console.log('✅ Done signal received');
                                        streamDone = true;
                                        // Final scroll to ensure full response is visible
                                        setTimeout(() => {
                                            chatMessages.scrollTop = chatMessages.scrollHeight;
                                        }, 200);
                                        // Break out of the line processing loop
                                        break;
                                    }
                                } catch (e) {
                                    console.error('Error parsing SSE data:', e);
                                }
                            }
                        }
                    }
                    
                    console.log('📊 Total chunks processed:', chunkCount);
                    
                } catch (error) {
                    console.error('Error:', error);
                    document.getElementById(responseId).textContent = 'Tyvärr, ett fel uppstod. Försök igen.';
                }
            }
            
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }
            
            // No prefetch - simple chat interface
            const messageInputEl = document.getElementById('messageInput');
            const userIdEl = document.getElementById('userId');
            
            // Funktion för att söka efter gamla konversationer
            async function searchHistory() {
                const userId = document.getElementById('userId').value.trim();
                const dateInput = document.getElementById('dateSearch').value;
                
                if (!userId || !dateInput) {
                    alert('Ange både användar-ID och datum (YYYY-MM-DD)');
                    return;
                }
                
                try {
                    const response = await fetch(`/chat/history/${userId}/date/${dateInput}`);
                    const data = await response.json();
                    
                    if (data.count > 0) {
                        alert(`Hittade ${data.count} konversationer från ${dateInput}`);
                        console.log('Historik:', data.conversations);
                    } else {
                        alert('Inga konversationer hittades för det datumet');
                    }
                } catch (error) {
                    console.error('Error searching history:', error);
                    alert('Fel vid sökning av historik');
                }
            }
            
            // Funktion för att visa personlighet
            async function showPersona() {
                const userId = document.getElementById('userId').value.trim();
                const personaDisplay = document.getElementById('personaDisplay');
                
                if (!userId) {
                    alert('Ange användar-ID först');
                    return;
                }
                
                personaDisplay.value = 'Laddar personlighet...';
                
                try {
                    const response = await fetch(`/memory/persona/${userId}`);
                    const data = await response.json();
                    
                    if (data.has_persona) {
                        personaDisplay.value = `Personlighet (${data.persona_length} tecken):\n\n${data.persona_profile}\n\nSenast uppdaterad: ${data.persona_last_updated}\nTid sedan uppdatering: ${data.time_since_update}s`;
                    } else {
                        personaDisplay.value = 'Ingen personlighet hittad. Klicka "Uppdatera" för att bygga en från Brain-data.';
                    }
                } catch (error) {
                    console.error('Error fetching persona:', error);
                    personaDisplay.value = 'Fel vid hämtning av personlighet: ' + error.message;
                }
            }
            
            // Funktion för att uppdatera personlighet
            async function refreshPersona() {
                const userId = document.getElementById('userId').value.trim();
                const personaDisplay = document.getElementById('personaDisplay');
                
                if (!userId) {
                    alert('Ange användar-ID först');
                    return;
                }
                
                personaDisplay.value = 'Uppdaterar personlighet...';
                
                try {
                    const response = await fetch(`/memory/persona/${userId}/refresh`, {
                        method: 'POST'
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        personaDisplay.value = `Personlighet uppdaterad (${data.persona_length} tecken):\n\n${data.persona_profile}\n\nUppdaterad: ${new Date().toLocaleString('sv-SE')}`;
                    } else {
                        personaDisplay.value = `Kunde inte uppdatera personlighet: ${data.message}`;
                    }
                } catch (error) {
                    console.error('Error refreshing persona:', error);
                    personaDisplay.value = 'Fel vid uppdatering av personlighet: ' + error.message;
                }
            }
        </script>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Hälsokontroll för applikationen."""
    return {
        "status": "healthy",
        "service": "Lumia",
        "version": "0.1.0"
    }


@app.get("/info")
async def get_info():
    """Hämta information om applikationen."""
    return {
        "name": "Lumia",
        "description": "Lokal AI-chattjänst med personligt minne",
        "version": "0.1.0",
        "features": [
            "Chatbaserad användarupplevelse",
            "Användarspecifikt minne",
            "Parallell RAG-analys",
            "Säker och lokal datalagring"
        ],
        "services": {
            "ollama": settings.ollama_base_url,
            "brain": settings.brain_api_url,
            "llm_model": settings.llm_model,
            "embedding_model": settings.embedding_model
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 