# Vision Assistant

Assistant multimodal temps reel pour analyser des images, repondre a des questions contextuelles et generer des reponses vocales.

## Vue d'ensemble

Vision Assistant expose une API FastAPI avec endpoints REST et WebSocket pour :
- analyse d'image et description de scene via Gemini
- questions contextuelles sur la derniere scene
- generation de reponses vocales
- streaming temps reel avec cache et reduction d'appels API

## Stack technique

- Python, FastAPI, Uvicorn
- Google Gemini (vision + chat)
- WebSocket pour le streaming
- Cache en memoire + nettoyage asynchrone

## Structure du projet

- `app/main.py` : point d'entree FastAPI
- `app/config.py` : configuration centralisee
- `app/api/` : endpoints REST
- `app/websocket/` : endpoints WebSocket
- `app/cache/` : cache d'images + taches de nettoyage
- `models/` : poids ou artefacts ML (optionnel)
- `temp/` : stockage temporaire
- `logs/` : logs applicatifs

## Prerequis

- Python 3.11 recommande
- Cle API Gemini

## Installation

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Variables d'environnement (exemple minimal) :

```
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-1.5-pro
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

## Lancer en local

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Endpoints utiles :
- `GET /` : statut
- `GET /docs` : Swagger
- `POST /api/v1/process-frame`
- `POST /api/v1/ask`
- `GET /api/v1/health`
- `WS /ws/stream`

## Deploiement Railway

Configuration recommande :
- Build: detection auto Python (Nixpacks)
- Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Variables Railway :
- `GEMINI_API_KEY` (obligatoire)
- `GEMINI_MODEL` (optionnel)
- `CORS_ORIGINS` (optionnel)
- `API_RELOAD=false` (recommande en prod)

Notes :
- `temp/` et `logs/` sont crees automatiquement au demarrage
- Le port doit provenir de `$PORT`

## Tests

```bash
python -m pytest
```
