---
name: "Eval task suggestion"
about: "Suggest a prompt for the held eval suite"
title: "Eval task: <one-line summary>"
labels: ["eval", "enhancement"]
---

The eval suite at [`eval/tasks.yaml`](../../eval/tasks.yaml) gates
every release. Each task is a prompt + a regex contract that the
plugin's response must satisfy.

**The prompt** (phrased so the model has to *reach* for the C++26
idiom unprompted — avoid mentioning C++26 / paper IDs directly):

> *your prompt here*

**Expected idiom** (which paper / feature should the response use?):

- Paper: P####
- Headline construct: …

**Suggested regex gates**:

```yaml
must_contain: ["..."]
must_not_contain: ["..."]
```

**Why this is a good test**: what pre-C++26 default does a vanilla
LLM emit for this prompt, and what does the plugin need to do
differently to satisfy the gates?
