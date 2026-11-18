# Updating the remote frontend

The local Vite server on port 5173 serves current React source with hot updates.
The remote website uses a separate production build of that same source:

```text
Cloudflare Tunnel -> 127.0.0.1:18764 -> windmind_remote_proxy.cjs
                                      -> .windmind-remote-dist/index.html
                                      -> .windmind-remote-dist/assets/*
```

`/cnn-monitor` is served from this build, not proxied to port 5173.
After changing frontend source, run this command from the website directory:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build_worker_remote.ps1
```

The proxy reads files from disk for each request and sends `Cache-Control: no-store`.
A frontend-only deployment needs no proxy, API, or Tunnel restart. Reload any open
browser tab to load the newly hashed JavaScript bundle. Keep the existing Tunnel
running to preserve its temporary hostname and Firebase authorized-domain entry.

For verification, compare the JavaScript asset referenced by `/cnn-monitor` at
`http://127.0.0.1:18764` and at the current external URL recorded in
`.windmind-logs/remote-tunnel-url.txt`. Both must match the asset on disk.
The CNN Power card should contain `unit: mW` and display watts multiplied by 1000;
for example, the existing API value `0.125` renders as `125 mW`. This is a display
conversion and does not change predictor formulas, API fields, or stored values.
