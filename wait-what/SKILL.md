---
name: wait-what
description: Re-explain the assistant's last message with missing context and simpler language when the user says they did not understand it. Invoke when the user says "what?" or "wait what?" or "no idea what you are talking about"
---

When the user says the last explanation did not land, re-explain it with the missing context. Use ASD-STE100 Simplified Technical English and the terms in `glossary.json` when that file exists.
