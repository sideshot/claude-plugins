# Product Studio - Image Generation

AI-powered product image generation for e-commerce.

## Workflow

1.  **Search**: Finds reference images via Tavily based on your subject.
2.  **Fetch**: Downloads the first reference image via ScrapeNinja.
3.  **Generate**: Uses Gemini 3 Pro to generate a new image, using the reference image for structural accuracy and applying your style instructions.
4.  **Save**: Outputs generated PNG and saves reference image for verification.

## Setup

Set environment variables:

```bash
export TAVILY_API_KEY="..."
export SCRAPENINJA_API_KEY="..."
export GEMINI_API_KEY="..."
```

## Usage

Run the script using `uv`:

```bash
uv run skills/image-generation/scripts/product_studio.py \
  --subject "Modern kitchen faucet installation diagram" \
  --style-instructions "Technical illustration, white background, labeled" \
  --resolution 2k \
  --aspect-ratio 21:9 \
  --output "assets/generated/"
```

### Parameters

- `--subject`: Search query and image topic. Be specific (include Brand, Model, Type).
- `--style-instructions`: Formatting and visual style directives.
- `--resolution`: `1k`, `2k`, `4k`.
- `--aspect-ratio`: `21:9` (default), `16:9`, `4:3`, `1:1`.
- `--debug`: Enable verbose logging of prompts and responses.

## Reference

See `skills/image-generation/SKILL.md` for detailed integration guide.
