---
name: Image Generation
description: This skill should be used when the user asks to "generate product images", "create infographics", "make exploded view diagrams", "create marketing shots", "generate e-commerce visuals", "build product diagrams", or mentions image generation for products. Provides guidance on using the product_studio.py script.
version: 0.2.1
---

# Product Image Generation

Generate professional product images using the `product_studio.py` script.

## Usage

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/image-generation/scripts/product_studio.py \
  --subject "[Brand] [Model] [product type] exploded view" \
  --style-instructions "Technical diagram style, white background, clean lines" \
  --resolution 2k \
  --aspect-ratio 21:9 \
  --output "assets/generated/" \
  --debug
```

## Parameters

### --subject (required)
Product/component description for search and generation. This is used as the Tavily search query and the primary image description for Gemini.

**Good subjects:**
- `"[Brand] [Model] [product type] exploded view components"`
- `"[Brand] [Series] [product category] installation diagram"`
- `"[product type] mechanism cross section"`

### --style-instructions (optional)
Format and style directives appended to the generation prompt.

**Examples:**
- `"Technical diagram style, white background, labeled components"`
- `"Marketing shot with soft shadows, professional lighting, brand color accents"`
- `"Clean infographic, side-by-side comparison"`

### --resolution (optional)
Output resolution. Default: `1k`
- `1k` (Draft)
- `2k` (Web/Production)
- `4k` (Print)

### --aspect-ratio (optional)
Output aspect ratio. Default: `21:9`
Options: `1:1`, `4:3`, `3:4`, `16:9`, `9:16`, `21:9`, `3:2`, `2:3`

### --output (optional)
Output directory. Default: `assets/generated/`

### --debug (optional)
Print detailed prompts and API responses to stderr.

## Output

Returns JSON:
```json
{
  "status": "success",
  "files": ["assets/generated/product_20251226_143022_0.png"],
  "reference_images": ["assets/generated/.refs/ref_20251226_143022_0.jpg"],
  "token_usage": {"input": 415, "output": 1502, "total": 1917},
  "message": "Generated 1 image(s)"
}
```

## Workflow

1. **Search** - Tavily image search using `--subject`
2. **Fetch** - Download first reference image via ScrapeNinja
3. **Generate** - Gemini creates image using reference image context
4. **Save** - Output files and reference image saved

## Required Environment Variables

```bash
export TAVILY_API_KEY="..."      # Image search
export SCRAPENINJA_API_KEY="..." # Image fetching
export GEMINI_API_KEY="..."      # Image generation
```
