# Stage 3: Reader Testing - Detailed Guide

## Goal

Test document with a fresh Claude (no context bleed) to verify it works for readers. Catches blind spots - things that make sense to authors but confuse others.

---

## With Sub-Agent Access (Claude Code)

Perform testing directly without user involvement.

### Step 1: Predict Reader Questions

"Predicting what questions readers might ask when discovering this document..."

Generate 5-10 realistic questions readers would ask.

### Step 2: Test with Sub-Agent

"Testing these questions with a fresh Claude instance (no context from our conversation)..."

For each question:
- Invoke sub-agent with ONLY the document content + question
- Summarize what Reader Claude got right/wrong

### Step 3: Additional Checks

"Running additional checks..."

Invoke sub-agent to check for:
- Ambiguity
- False assumptions
- Contradictions

Summarize any issues found.

### Step 4: Report and Fix

If issues found:
```
Reader Claude struggled with:
- [Issue 1]
- [Issue 2]

Fixing these gaps now...
```

Loop back to Stage 2 for problematic sections.

---

## Without Sub-Agent Access (claude.ai web)

User performs testing manually.

### Step 1: Predict Reader Questions

"What questions might people ask when trying to discover this document? What would they type into Claude.ai?"

Generate 5-10 realistic questions.

### Step 2: Setup Testing

Provide instructions:

1. Open fresh Claude: https://claude.ai
2. Paste/share document content
3. Ask Reader Claude generated questions

For each question, have Reader Claude provide:
- The answer
- Whether anything was ambiguous or unclear
- What knowledge the doc assumes reader has

Check if Reader Claude gives correct answers or misinterprets.

### Step 3: Additional Checks

Also ask Reader Claude:
- "What in this doc might be ambiguous or unclear to readers?"
- "What knowledge or context does this doc assume readers already have?"
- "Are there any internal contradictions or inconsistencies?"

### Step 4: Iterate Based on Results

"What did Reader Claude get wrong or struggle with? I'll fix those gaps."

Loop back to Stage 2 for problematic sections.

---

## Exit Condition

Reader Testing passes when:
- Reader Claude consistently answers questions correctly
- No new gaps or ambiguities surfaced

---

## Final Review

When testing passes:

"✅ Doc passed Reader Claude testing. Before we wrap up:"

1. Recommend final read-through by user - they own this document
2. Suggest double-checking facts, links, technical details
3. Ask to verify it achieves the intended impact

"Want one more review, or are we done?"

If final review requested → provide it.

Otherwise:

"📄 Document complete! Final tips:
- Consider linking this conversation in an appendix
- Use appendices to provide depth without bloating main doc
- Update as you receive feedback from real readers"
