---
description: Generate product images for e-commerce (infographics, diagrams, marketing shots)
argument-hint: [image-reference-query]
allowed-tools: Read, Bash, Glob, Grep
---

# Product Image Generation

Generate product images using the product_studio.py script.

## Pre-Flight Checks

1. **Verify environment variables** are set:
   - `TAVILY_API_KEY` - Image search
   - `SCRAPENINJA_API_KEY` - Image fetching
   - `GEMINI_API_KEY` - Image generation
   - `ANTHROPIC_API_KEY` - Reference selection

2. **Create output directory**:
   ```bash
   mkdir -p assets/generated
   ```

3. **Locate brand guidelines** (if available):
   - Search for `brand-guidelines` skill
   - Look for `.claude/brand-guidelines.md`
   - If not found, ask user for brand colors

## Script Invocation

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/image-generation/scripts/product_studio.py \
  --image-reference-query "[BRAND] [SERIES] [PRODUCT TYPE] [VIEW TYPE]" \
  --prompt-image-creation-needs '{"colors": ["#hex1", "#hex2"], "style": "...", "labels": [...]}' \
  --extra-gen-parameters '{"ratio": "21:9", "detail": "1k", "count": 1}' \
  --output "assets/generated/"
```

## Parameters

### --image-reference-query (required)
Search query for finding reference images. **This is also the image description.**

Template: `"[BRAND] [SERIES] [PRODUCT TYPE] [VIEW TYPE]"`

### --prompt-image-creation-needs (required)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `colors` | array | Yes | Hex color codes from brand guidelines |
| `style` | string | Yes | `"technical diagram"`, `"infographic"`, `"marketing shot"`, `"educational"` |
| `labels` | array | No | Text labels to include. Omit for no text. |
| `ascii_sketch` | string | No | Layout guide for composition |

**Clean product shot** (no text):
```json
{"colors": ["#333333", "#ffffff"], "style": "marketing shot"}
```

**Technical diagram with labels**:
```json
{"colors": ["#dc2626", "#333333"], "style": "technical diagram", "labels": ["Component A", "Component B"]}
```

### --extra-gen-parameters (optional)

| Field | Default | Options |
|-------|---------|---------|
| `ratio` | `"21:9"` | `"1:1"`, `"3:4"`, `"4:3"`, `"9:16"`, `"16:9"`, `"21:9"` |
| `detail` | `"1k"` | `"1k"` (draft), `"2k"` (production), `"4k"` (print) |
| `count` | `1` | Number of images |

## Output

Script returns JSON:
```json
{
  "status": "success",
  "files": ["assets/generated/product_001.png"],
  "reference_images": ["assets/generated/.refs/ref_0.jpg"],
  "token_usage": {"input": 1200, "output": 800},
  "message": "Generated 1 image successfully"
}
```

## Error Handling

| Error | Resolution |
|-------|------------|
| No reference images found | Broaden search terms, remove model numbers |
| Wrong product generated | Be more specific, add `"NOT [unwanted]"` |
| Unwanted text in image | Omit `labels` field entirely |
| Quality too low | Increase detail to `"2k"` or `"4k"` |
