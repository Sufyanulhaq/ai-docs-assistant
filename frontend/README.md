# Front end

Next.js (App Router, TypeScript, Tailwind) chat UI for the AI Docs Assistant.

It streams answers from the Python backend through the proxy routes in `app/api/`, so the browser never contacts the backend directly.

```bash
npm install
cp .env.example .env.local   # BACKEND_URL defaults to http://localhost:8000
npm run dev
```

See the [project README](../README.md) for the full setup.
