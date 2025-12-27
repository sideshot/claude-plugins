# Troubleshooting

## Common Issues

### 1. No Reference Images Found
**Error**: `No reference images found for query: '...'`
**Cause**: Tavily search returned zero results.
**Fix**:
- Simplify the `--subject`.
- Remove specific model numbers if they are obscure (e.g., use "Soft close hinge" instead of "Brand Model 12345").
- Check internet connection and `TAVILY_API_KEY`.

### 2. Fetching Failed
**Error**: `Failed to fetch any reference images`
**Cause**: ScrapeNinja could not download the image URL provided by Tavily.
**Fix**:
- Rerun the command (sometimes transient network issue).
- Check `SCRAPENINJA_API_KEY`.
- Try a broader subject to find different source images.

### 3. Gemini Generation Failed
**Error**: `Gemini generation returned no images`
**Cause**: Safety filters or prompt complexity.
**Fix**:
- Check `GEMINI_API_KEY`.
- Simplify `--style-instructions`.
- Use `--debug` to see exactly what is being sent to Gemini.

### 4. Wrong Product / Inaccurate Image
**Issue**: Generated image doesn't match the specific model.
**Cause**: The reference image found was incorrect or Gemini hallucinated details.
**Fix**:
- Use `--debug` to check the reference image URL/description.
- Be MORE specific in `--subject` (e.g., "Frameless cabinet hinge" vs just "Cabinet hinge").
- Add descriptive constraints to `--style-instructions`.

### 5. Text / Labels are Garbled
**Issue**: Text in the image is unreadable pseudo-text.
**Fix**:
- Gemini is better at text than most, but not perfect.
- Add `"No text labels"` to `--style-instructions` if you want a clean image to label later in Photoshop/Figma.
- If you need labels, be explicit: `"Labeled components with clear English text"`.

## Debugging

Use the `--debug` flag to see the full prompt chain:

```bash
uv run .../product_studio.py --subject "..." --debug
```

This prints:
1. **Search Results**: Count of candidates.
2. **Gemini Parts Structure**: Exact text prompt and image placement.
3. **Gemini Response**: Text feedback from model.
