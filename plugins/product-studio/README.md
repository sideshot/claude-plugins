# product-studio

AI-powered product image generation for e-commerce using a structured workflow:

**Search → Reference → Brand → Create → Verify**

## Features

- Generate infographics, exploded views, marketing shots, technical diagrams
- Automatic reference image discovery via Tavily
- Smart image selection using Claude Haiku (consensus + clarity)
- Brand-aware generation with user's brand guidelines
- Support for ASCII sketches as generation guidance
- Multiple aspect ratios: 1:1, 3:4, 4:3, 9:16, 16:9, 21:9

## Prerequisites

### Required Environment Variables

```bash
export TAVILY_API_KEY="your-tavily-api-key"
export SCRAPENINJA_API_KEY="your-scrapeninja-api-key"
export GEMINI_API_KEY="your-gemini-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

Get your API keys from:
- Tavily: https://tavily.com
- ScrapeNinja: https://rapidapi.com/restyler/api/scrapeninja
- Gemini: https://aistudio.google.com/apikey
- Anthropic: https://console.anthropic.com

### Required Tools

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager

## Quick Start

### Direct Script Usage

```bash
uv run skills/image-generation/scripts/product_studio.py \
  --image-reference-query "[BRAND] [SERIES] [PRODUCT TYPE] exploded view components" \
  --prompt-image-creation-needs '{"colors": ["#0066cc", "#333333"], "style": "technical diagram", "labels": ["Component A", "Component B", "Component C"]}' \
  --output "assets/generated/"
```

### Via Claude Code Command

```bash
/product-studio:generate
```

## Parameters

The command accepts:
- **image-reference-query**: Search query for finding reference images
- **prompt-image-creation-needs**: JSON with `colors`, `style`, `labels` (optional), `ascii_sketch` (optional)
- **extra-gen-parameters**: Gemini parameters (ratio, detail, count)
- **output**: Output directory (default: `assets/generated/`)

## Output

Generated images are saved to `assets/generated/` along with:
- Reference images used (for debugging)
- Generation metadata

## Brand Guidelines

The plugin looks for a `brand-guidelines` skill or similar to extract:
- Brand colors (hex codes)
- Style preferences
- Target audience

If not found, the agent will ask for brand information.

## Supported Image Types

- Product infographics
- Exploded view diagrams
- Marketing/lifestyle shots
- Technical diagrams
- Comparison charts
- Component breakdowns

## Aspect Ratios

| Ratio | Use Case |
|-------|----------|
| 21:9 | Ultrawide banners (default) |
| 16:9 | Standard widescreen |
| 4:3 | Traditional format |
| 3:4 | Portrait format |
| 1:1 | Square (social media) |
| 9:16 | Vertical/mobile |

## Detail Levels

- **1k** (default): Fast generation, good for drafts
- **2k**: Balanced quality and speed
- **4k**: Highest quality, slower generation
