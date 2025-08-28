# Lumia Setup Guide

## Förutsättningar

1. **Python 3.8+** installerat
2. **Ollama** installerat och körande
3. **Brain-tjänst** körande på `http://127.0.0.1:8000`

## Snabbstart

### 1. Installera dependencies

```bash
pip install -r requirements.txt
```

### 2. Konfigurera miljövariabler

Kopiera exempel-filen och anpassa:

```bash
cp env.example .env
```

Redigera `.env`-filen efter behov:

```env
# Ollama-inställningar
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=gemma3:12b
EMBEDDING_MODEL=nomic-embed-text

# Brain API (din befintliga tjänst)
BRAIN_API_URL=http://127.0.0.1:8000

# Lumia-applikation
PORT=8002
HOST=0.0.0.0
DEBUG=True
```

### 3. Ladda ner Ollama-modeller

```bash
# LLM-modell för chatt
ollama pull gemma3:12b

# Embedding-modell för Brain
ollama pull nomic-embed-text
```

### 4. Starta Lumia

```bash
# Alternativ 1: Använd startskriptet
./start_lumia.py

# Alternativ 2: Direkt med uvicorn
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

### 5. Testa installationen

```bash
./test_lumia.py
```

## Användning

### Web-interface

Öppna webbläsaren och gå till:
```
# Lokalt
http://localhost:8002

# Från annan maskin på samma nätverk
http://192.168.1.100:8002  # Ersätt med din lokala IP
```

### API-anrop

```bash
# Testa chatt
curl -X POST "http://localhost:8002/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hej! Vad är Lumia?",
    "user_id": "lumia_test_user"
  }'

# Hälsokontroll
curl http://localhost:8002/health

# Applikationsinfo
curl http://localhost:8002/info
```

### API-dokumentation

Interaktiv dokumentation finns på:
```
http://localhost:8002/docs
```

## Arkitektur

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Lumia App     │    │   Brain Service │
│   (lokalt nät)  │◄──►│   (0.0.0.0)     │◄──►│   (127.0.0.1)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Ollama LLM    │
                       │  (Port 11434)   │
                       └─────────────────┘
```

## Säkerhet för lokalt nätverk

För att säkra åtkomst till lokalt nätverk, konfigurera UFW:

```bash
# Kontrollera UFW-status
sudo ufw status

# Aktivera UFW (om inte redan aktiverat)
sudo ufw enable

# Tillåt lokalt nätverk
sudo ufw allow from 192.168.0.0/16 to any port 8002
sudo ufw allow from 10.0.0.0/8 to any port 8002
sudo ufw allow from 172.16.0.0/12 to any port 8002
sudo ufw allow from 127.0.0.1 to any port 8002
```

Se `SECURITY.md` för detaljerad säkerhetsguide.

## Felsökning

### Ollama-problem

```bash
# Kontrollera att Ollama körs
curl http://localhost:11434/api/tags

# Kontrollera tillgängliga modeller
ollama list
```

### Brain-tjänst problem

```bash
# Kontrollera Brain-hälsa
curl http://127.0.0.1:8000/health

# Testa Brain-API
curl -X POST "http://127.0.0.1:8000/collections" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "test", "description": "Test"}'
```

### Port-konflikter

Om port 8002 är upptagen, ändra i `.env`:

```env
PORT=8003
```

## Utveckling

### Projektstruktur

```
lumia/
├── app/                    # Huvudapplikation
│   ├── api/               # API endpoints
│   ├── core/              # Konfiguration
│   ├── models/            # Data-modeller
│   └── services/          # Affärslogik
├── brain/                 # Brain-tjänst (separat)
├── tests/                 # Tester
├── main.py               # Huvudapplikation
├── start_lumia.py        # Startskript
└── test_lumia.py         # Testskript
```

### Lägga till nya funktioner

1. Skapa modeller i `app/models/`
2. Implementera tjänster i `app/services/`
3. Lägg till API-endpoints i `app/api/`
4. Uppdatera `main.py` med nya routers

## Nästa steg

- [ ] Implementera användarhantering med JWT
- [ ] Lägg till databas för användare
- [ ] Implementera kontextstrategier
- [ ] Skapa dashboard för historik
- [ ] Lägg till multi-agent support 