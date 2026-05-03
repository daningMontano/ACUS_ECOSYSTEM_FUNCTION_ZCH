# Stage 1: Context Gathering - Detailed Guide

## Initial Questions

Start by asking meta-context about the document:

1. **Document Type**: What type of document is this? (e.g., technical spec, decision doc, proposal)
2. **Audience**: Who's the primary audience?
3. **Impact**: What's the desired impact when someone reads this?
4. **Template**: Is there a template or specific format to follow?
5. **Constraints**: Any other constraints or context to know?

Inform them they can answer in shorthand or dump information however works best.

## Template Handling

**If user provides a template or mentions a doc type:**
- Ask if they have a template document to share
- If they provide a link → use appropriate integration to fetch it
- If they provide a file → read it

**If user mentions editing an existing shared document:**
- Use appropriate integration to read current state
- Check for images without alt-text
- If images exist without alt-text → explain Claude won't see them, offer to generate alt-text

## Info Dumping Phase

Encourage user to dump all context. Request:
- Background on the project/problem
- Related team discussions or shared documents
- Why alternative solutions aren't being used
- Organizational context (team dynamics, past incidents, politics)
- Timeline pressures or constraints
- Technical architecture or dependencies
- Stakeholder concerns

Advise: "Don't worry about organizing - just get it all out."

### Multiple Input Methods

Offer multiple ways to provide context:
- Info dump stream-of-consciousness
- Point to team channels or threads to read
- Link to shared documents

**If integrations available** (Slack, Teams, Google Drive, SharePoint, MCP servers):
- Mention these can pull in context directly

**If no integrations in Claude.ai/app:**
- Suggest enabling connectors in Claude settings
- Or paste relevant content directly

## Clarifying Questions

When user signals initial dump complete:

1. Generate 5-10 numbered questions based on gaps
2. Inform them: "You can use shorthand to answer (e.g., '1: yes, 2: see #channel')"
3. Allow linking more docs or continuing info dump

Track what's learned vs. what's still unclear.

## Exit Condition

Sufficient context when:
- Can ask about edge cases and trade-offs
- Don't need basics explained anymore

## Transition

Ask: "Any more context to provide, or ready to move to drafting?"

If user wants to add more → let them
When ready → proceed to Stage 2
