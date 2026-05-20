---
id: PFIX003
title: "Generic Senders (fixture)"
revision: R2
tier: shallow
category: concurrency
keywords: [sender, scheduler, async, std::execution]
canonical_url: https://example.invalid/PFIX003
---

# PFIX003 — Generic senders (fixture)

Senders model lazily-built async work that completes against a scheduler.
Replaces `std::async` for concurrent composition.
