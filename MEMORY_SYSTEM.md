# 🧠 Lumia Memory System

## Översikt

Lumia Memory System är ett intelligent minnessystem som bygger kontinuerligt på användarens konversationshistorik och personliga kontext. Systemet fungerar som ett "långsiktigt minne" som alltid är tillgängligt för AI:n, medan det samtidigt uppdateras i bakgrunden.

## 🎯 Koncept

### Kortsiktigt minne (Short-term Memory)
- **Innehåll**: Den aktuella konversationen (sista 5 utbyten)
- **Syfte**: Ge AI:n kontext om vad som just diskuterats
- **Uppdatering**: Omedelbar när varje meddelande skickas

### Långsiktigt minne (Long-term Memory)
- **Innehåll**: Användarens historiska konversationer och personliga kontext
- **Syfte**: Ge AI:n djupare förståelse för användarens preferenser, intressen och historik
- **Uppdatering**: Asynkront i bakgrunden medan AI:n svarar

### Realtidskontext (Real-time Context)
- **Innehåll**: Snabb sökning i Brain för aktuell kontext
- **Syfte**: Ge omedelbar kontext för snabba svar
- **Uppdatering**: Realtid med quick query (0.5-1 sekund)

## 🔄 Hur det fungerar

### 1. Snabb respons med hybrid context
```
Användare skickar meddelande
    ↓
AI använder kombinerad context:
- Cachat minne (kortsiktigt + långsiktigt)
- Realtidskontext (quick query, 0.5-1s)
    ↓
AI svarar omedelbart
```

### 2. Bakgrundsuppdatering med fullständig RAG
```
AI svarar
    ↓
Bakgrundsuppgifter startas:
- Lägg till i kortminne (omedelbar)
- Uppdatera långminne från Brain (full RAG, 3-6s)
- Spara konversation till Brain (0.1-0.5s)
```

## ⚡ Hybrid Context System

### Realtid (Quick Context)
- **Endpoint**: `/query/quick`
- **Svarstid**: 0.5-1 sekund
- **Funktion**: Returnerar bara search results utan LLM
- **Användning**: Omedelbar context för snabba svar

### Bakgrund (Full RAG)
- **Endpoint**: `/query`
- **Svarstid**: 3-6 sekunder
- **Funktion**: Fullständig RAG med LLM-svar
- **Användning**: Bättre context för långsiktigt minne

## 📊 API Endpoints

### Memory Chat
```bash
# Använd memory system för chat
POST /memory/chat/stream
{
  "message": "Hej, hur mår du?",
  "user_id": "user123"
}
```

### Memory Stats
```bash
# Se minnesstatistik för användare
GET /memory/stats/user123
```

### Clear Memory
```bash
# Rensa minne för användare
POST /memory/clear/user123
```

### Memory Health
```bash
# Kontrollera memory service status
GET /memory/health
```

## 🚀 Fördelar

### 1. **Snabb respons**
- AI svarar omedelbart med cachat minne + quick context
- Ingen väntan på fullständig RAG

### 2. **Kontinuerlig förbättring**
- Minnet uppdateras i bakgrunden med fullständig RAG
- Varje konversation bygger på tidigare

### 3. **Personlig kontext**
- AI kommer ihåg användarens preferenser
- Konversationer blir mer naturliga över tid

### 4. **Skalbarhet**
- Memory cache håller användare i minnet
- Bakgrundsuppdateringar påverkar inte respons

### 5. **Hybrid performance**
- Realtid: Quick context för snabba svar
- Bakgrund: Full RAG för bättre context

## 🔧 Teknisk implementation

### MemoryService
```python
class MemoryService:
    def __init__(self):
        self.memory_cache: Dict[str, MemoryContext] = {}
        self.update_tasks: Set[str] = set()
```

### MemoryContext
```python
@dataclass
class MemoryContext:
    user_id: str
    short_term: List[str]  # Aktuell konversation
    long_term: List[str]   # Historisk kontext
    last_updated: datetime
    is_updating: bool = False
```

## 📈 Performance

### Jämförelse med traditionell RAG:
- **Traditionell RAG**: 6-9 sekunder (Brain query + LLM)
- **Memory System (hybrid)**: 0.5-2 sekunder (cachat + quick context)
- **Bakgrundsuppdatering**: 3-6 sekunder (full RAG)

### Context timing:
- **Cachat minne**: Omedelbar
- **Realtidskontext**: 0.5-1 sekund (quick query)
- **Långsiktigt minne**: 3-6 sekunder (full RAG, bakgrund)
- **Brain save**: 0.1-0.5 sekunder (bakgrund)

## 🎯 Användningsfall

### 1. **Personlig assistent**
- Kommer ihåg användarens preferenser
- Bygger på tidigare konversationer
- Snabba svar med relevant context

### 2. **Kundsupport**
- Känner igen återkommande frågor
- Ger personlig service
- Omedelbar hjälp med quick context

### 3. **Lärande system**
- Anpassar sig efter användarens kunskapsnivå
- Bygger på tidigare lektioner
- Snabba svar med relevant information

## 🔄 Arbetsflöde

```
1. Användare skickar meddelande
   ↓
2. MemoryService hämtar:
   - Cachat minne (omedelbar)
   - Realtidskontext (quick query, 0.5-1s)
   ↓
3. AI genererar svar med kombinerad context
   ↓
4. Svar streamas till användare
   ↓
5. Bakgrundsuppgifter startas:
   - Lägg till i kortminne (omedelbar)
   - Uppdatera långminne från Brain (full RAG, 3-6s)
   - Spara till Brain för framtida användning
```

## 🛠️ Konfiguration

### Environment Variables
```bash
# Memory cache settings
MEMORY_CACHE_SIZE=1000
MEMORY_SHORT_TERM_LIMIT=5
MEMORY_LONG_TERM_LIMIT=10

# Brain API settings
BRAIN_API_URL=http://127.0.0.1:8000
```

## 📝 Exempel

### Första konversationen
```
Användare: "Hej, jag heter Jonas"
AI: "Hej Jonas! Trevligt att träffas!"
Memory: Sparar i kortminne, quick context för realtid
```

### Andra konversationen
```
Användare: "Vad kommer du ihåg om mig?"
AI: "Jag kommer ihåg att du heter Jonas!"
Memory: Använder kortminne + quick context, uppdaterar långminne med full RAG
```

### Senare konversationer
```
Användare: "Berätta om mina intressen"
AI: "Baserat på våra tidigare konversationer..."
Memory: Använder både kort- och långminne + quick context
```

## 🎯 Framtida förbättringar

1. **Memory persistence** - Spara minne till disk
2. **Memory compression** - Komprimera gamla minnen
3. **Memory search** - Sök i historiska minnen
4. **Memory analytics** - Analysera minnesanvändning
5. **Multi-user memory** - Dela minnen mellan användare
6. **Context prioritization** - Prioritera viktig context
7. **Adaptive quick queries** - Anpassa quick query baserat på användning 