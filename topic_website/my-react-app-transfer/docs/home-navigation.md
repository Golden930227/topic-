# Home navigation

The main `/ai-model` route imports the standalone AI app's `src/App.jsx`.
Both share the same brand link; its appearance is unchanged.

- AI frontend: set `VITE_HOME_URL` at build time for a separately hosted main site.
  Without it, navigation uses `/` on the current origin. In Vite development on
  port 5174, it uses the same hostname on port 5173.
- FastAPI: set `WINDMIND_HOME_URL` to the main site's HTTP(S) URL or a site-relative
  path. Without it, `/docs` uses `/` on its current origin, except local development
  on port 8000, which uses the same hostname on port 5173.

For separate production origins, configure both values to the deployed main site.
The API docs retain FastAPI's Swagger assets, OpenAPI URL, OAuth redirect and
interactive operations. Only the title text becomes a native link; version
badges remain unchanged. Both links support Tab/Enter and a visible focus outline.
