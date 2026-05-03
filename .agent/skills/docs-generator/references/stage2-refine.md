# Stage 2: Refinement & Structure - Detailed Guide

## Overview

Build document section by section through:
1. Clarifying questions
2. Brainstorming options
3. User curation
4. Drafting
5. Iterative refinement

## Section Ordering

**If structure is clear:**
- Ask which section to start with
- Suggest starting with the most unknown section
- Decision docs → core proposal first
- Specs → technical approach first
- Summary sections → last

**If user doesn't know sections needed:**
- Suggest 3-5 appropriate sections based on doc type
- Ask if structure works or needs adjustment

## Initial Document Scaffold

Once structure agreed:

**With artifacts:**
```
Use create_file to create artifact with:
- All section headers
- Placeholder text: "[To be written]"
```

**Without artifacts:**
```
Create markdown file (e.g., decision-doc.md, technical-spec.md)
- All section headers
- Placeholder text
```

## For Each Section

### Step 1: Clarifying Questions

"Working on [SECTION NAME]. Here are some questions about what to include:"

Generate 5-10 specific questions based on:
- Context gathered in Stage 1
- Section purpose
- Gaps in understanding

"Answer in shorthand or indicate what's important to cover."

### Step 2: Brainstorming

"For [SECTION NAME], here are [5-20] things that might be included:"

Generate numbered options looking for:
- Context shared that might have been forgotten
- Angles or considerations not yet mentioned

End with: "Want me to brainstorm more options?"

### Step 3: Curation

Ask which points to keep/remove/combine with brief justifications.

Example responses:
- "Keep 1,4,7,9"
- "Remove 3 (duplicates 1)"
- "Remove 6 (audience already knows this)"
- "Combine 11 and 12"

**If user gives freeform feedback** (e.g., "looks good"):
- Parse their preferences
- Apply what they want kept/removed/changed

### Step 4: Gap Check

"Based on what you've selected, anything important missing for [SECTION NAME]?"

### Step 5: Drafting

Use `str_replace` to replace placeholder with drafted content.

**First section only - include this note:**
> Instead of editing the doc directly, indicate what to change. This helps me learn your style for future sections.
> Example: "Remove the X bullet - already covered by Y" or "Make the third paragraph more concise"

### Step 6: Iterative Refinement

As user provides feedback:
- Use `str_replace` for edits (never reprint whole doc)
- Provide artifact link after each edit
- If user edits directly → note their preferences for future sections

**After 3 consecutive iterations with no substantial changes:**
- Ask if anything can be removed without losing important info

When section done: "✅ [SECTION NAME] complete. Ready for next section?"

## Near Completion (80%+)

Announce intention to re-read entire document and check for:
- Flow and consistency across sections
- Redundancy or contradictions
- "Slop" or generic filler
- Whether every sentence carries weight

Provide feedback and final suggestions.

## All Sections Complete

"All sections drafted. Reviewing complete document one more time..."

Review for: overall coherence, flow, completeness.

Ask: "Ready for Reader Testing, or want to refine anything else?"
