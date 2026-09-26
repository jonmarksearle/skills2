---
name: wait-what
description: Re-explain the assistant's last message with missing context and simpler language when the user says they did not understand it.
---

When the user says the last explanation did not land, re-explain it with the missing context. Use ASD-STE100 Simplified Technical English and the terms in `CONTEXT.md` when that file exists. If the repository has `CONTEXT-MAP.md`, use it to find the relevant context file.
