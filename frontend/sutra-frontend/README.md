# SUTRA Frontend

This is the UI surface for the SUTRA demo:

- owner dashboard
- mobile approval app
- supplier portal

## Run locally

1. Install dependencies.

```bash
npm install
```

2. Start the app.

```bash
npm run dev
```

3. By default the frontend talks to `http://localhost:8000`.

If you want to override the backend URL:

```bash
set VITE_SUTRA_API_BASE_URL=http://localhost:8000
```

## Routes

- `/` - dashboard
- `/mobile` - mobile approval view
- `/supplier` - supplier portal

## Backend expectations

The frontend expects these backend endpoints:

- `GET /analytics/summary`
- `POST /voice/process`
- `POST /procurement/approve`
- `POST /procurement/reject`
- websocket: `/ws/dashboard`
- websocket: `/ws/supplier`

## Demo scope

For the hackathon demo, the safe path is:

- rice only
- local backend
- local ML
- local mobile Whisper
- no cloud dependency

## Notes

- The frontend is designed to show graceful fallback states if the backend is slow or unavailable.
- The mobile app is multilingual and should be connected to local Whisper for voice input.
