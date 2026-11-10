# UNKNOWN CYBER SUITE

A cyber-themed CLI + animated local dashboard inspired by the uploaded reference.

## Features
- Interactive terminal menu
- Animated network topology and decorative radar
- Local system snapshot (hostname, OS, CPU, memory, uptime)
- Demo activity feed
- No external services or API keys required

## Run
Requires Python 3.9+.

```bash
python unknown_cyber_suite.py
```

Choose `1` to launch the dashboard. It opens at http://127.0.0.1:8765.
Press Ctrl+C in the terminal to stop it.

Optional accurate CPU/RAM readings:
```bash
python -m pip install psutil
```

## Safety and scope
This is a local-only educational/defensive visualization. It does not scan networks,
send traffic to targets, perform DDoS, exploit systems, collect credentials, or
interact with remote hosts. The web server binds only to 127.0.0.1.
