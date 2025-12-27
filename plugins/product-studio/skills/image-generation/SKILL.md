---
name: Image Generation
description: This skill should be used when the user asks to "generate product images", "create infographics", "make exploded view diagrams", "create marketing shots", "generate e-commerce visuals", "build product diagrams", or mentions image generation for products. Provides guidance on using the product_studio.py script.
version: 0.1.0
---

# Product Image Generation

Generate professional product images using the `product_studio.py` script.

## Usage

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/image-generation/scripts/product_studio.py \
  --image-reference-query "SEARCH QUERY" \
  --prompt-image-creation-needs '{"colors": [...], "style": "...", ...}' \
  --extra-gen-parameters '{"ratio": "21:9", "detail": "1k", "count": 1}' \
  --output "assets/generated/"
```

## Parameters

### --image-reference-query (required)
Search query to find reference images. **This is also the image description** - be specific.

**Query template:** `"[BRAND] [SERIES] [CATEGORY] [VIEW TYPE]"`

Good queries:
- `"[Brand] [Model] [product type] exploded view components"`
- `"[Brand] [Series] [product category] installation diagram"`
- `"[product type] mechanism cross section"`

Bad queries:
- `"[product type]"` (too vague)
- `"product"` (useless)

### --prompt-image-creation-needs (required)
JSON object with these fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `colors` | array | Yes | Hex color codes: `["#dc2626", "#111827"]` |
| `style` | string | Yes | `"technical diagram"`, `"infographic"`, `"marketing shot"`, `"educational"` |
| `labels` | array | No | Text labels to include: `["Part A", "Part B"]`. Omit for no text. |
| `ascii_sketch` | string | No | Layout guide: `"[LEFT: Product] | [RIGHT: Features]"` |

**Examples:**

Clean product shot (no text):
```json
{"colors": ["#333333", "#ffffff"], "style": "marketing shot"}
```

Technical diagram with labels:
```json
{"colors": ["#dc2626", "#333333"], "style": "technical diagram", "labels": ["Component A", "Component B", "Bracket"]}
```

Infographic with layout:
```json
{"colors": ["#0066cc", "#ffffff"], "style": "infographic", "labels": ["Feature 1", "Feature 2"], "ascii_sketch": "[Product]--[Callout 1]\n         \\--[Callout 2]"}
```

### --extra-gen-parameters (optional)
JSON object for Gemini settings:

| Field | Default | Options |
|-------|---------|---------|
| `ratio` | `"21:9"` | `"1:1"`, `"3:4"`, `"4:3"`, `"9:16"`, `"16:9"`, `"21:9"` |
| `detail` | `"1k"` | `"1k"` (draft), `"2k"` (production), `"4k"` (print) |
| `count` | `1` | Number of images to generate |

### --output (optional)
Output directory. Default: `assets/generated/`

## Output

The script returns JSON:
```json
{
  "status": "success",
  "files": ["assets/generated/product_001.png"],
  "reference_images": ["assets/generated/.refs/ref_0.jpg"],
  "token_usage": {"input": 1200, "output": 800, "total": 2000},
  "message": "Generated 1 image successfully"
}
```

## Required Environment Variables

```bash
export TAVILY_API_KEY="..."      # Image search
export SCRAPENINJA_API_KEY="..." # Image fetching
export GEMINI_API_KEY="..."      # Image generation
export ANTHROPIC_API_KEY="..."   # Reference selection
```

## Common Issues

**No reference images found**: Broaden search terms, remove model numbers.

**Wrong product generated**: Be more specific in query, add exclusions like `"NOT [unwanted variant]"`.

**Unwanted text in image**: Omit `labels` field entirely for clean images.

**Quality too low**: Increase detail to `"2k"` or `"4k"`.

## References

- **`references/prompt-patterns.md`** - Example prompts by image type
- **`references/troubleshooting.md`** - Detailed error resolution
