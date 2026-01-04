# B1 Outreach and Response Note Template

This template is for logging outreach attempts and responses related to the B1 AI Growth Toolkit affiliate program.

---

```json
{
  "timestamp": "2025-12-01T12:00:00Z",
  "stream": "B1",
  "type": "outreach",  
  "contact": {
    "name": "[Creator or Newsletter Operator Name]",
    "platform": "[TikTok, Newsletter, Twitter, etc.]",
    "handle": "@[handle]",
    "email": "[email@example.com]"
  },
  "message_variant": "Variant 1 or Variant 2",
  "message_content": "[Full message sent]",
  "tracking_link": "https://b1.example.com/?aff_id=[affiliate_id]",
  "response": null
}
```

---

```json
{
  "timestamp": "2025-12-01T12:30:00Z",
  "stream": "B1",
  "type": "response",
  "contact": {
    "name": "[Creator or Newsletter Operator Name]",
    "platform": "[TikTok, Newsletter, Twitter, etc.]",
    "handle": "@[handle]",
    "email": "[email@example.com]"
  },
  "response_content": "[Response text]",
  "next_steps": "[Follow-up actions or notes]"
}
```

---

Use this template to append JSONL entries to memory/notes.jsonl for every outreach and response to maintain a durable record of affiliate interactions.