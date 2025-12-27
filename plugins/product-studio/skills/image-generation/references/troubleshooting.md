# Troubleshooting Guide

Solutions for common issues. Replace `[PLACEHOLDERS]` with actual values.

## Pre-Flight Errors

### Missing API Keys

**Error**: `TAVILY_API_KEY environment variable not set`

**Resolution**:
```bash
export TAVILY_API_KEY="your-key-here"
export SCRAPENINJA_API_KEY="your-key-here"
export GEMINI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
```

Get keys from:
- Tavily: https://tavily.com
- ScrapeNinja: https://rapidapi.com/restyler/api/scrapeninja
- Gemini: https://aistudio.google.com/apikey
- Anthropic: https://console.anthropic.com

### Output Directory Issues

**Error**: `Cannot create output directory`

**Resolution**:
```bash
mkdir -p assets/generated
chmod 755 assets/generated
```

Or use alternative path: `--output "/tmp/product-studio/"`

---

## Search Phase Errors

### No Reference Images Found

**Error**: `No reference images found for query`

**Resolution**:

1. **Broaden the query**:
   - Before: `"[BRAND] [MODEL]-[VARIANT] [PRODUCT TYPE]"`
   - After: `"[BRAND] [PRODUCT TYPE] exploded view"`

2. **Use category terms**:
   - Before: `"[MODEL NUMBER] component"`
   - After: `"[PRODUCT CATEGORY] mounting components"`

3. **Remove model numbers**:
   - Before: `"[MODEL]-[VARIANT] installation"`
   - After: `"[BRAND] [PRODUCT TYPE] installation diagram"`

4. **Provide ASCII sketch as fallback**:
   ```bash
   --image-reference-query "[PRODUCT TYPE] components"
   --prompt-image-creation-needs '{
     "colors": ["#333333", "#666666"],
     "style": "technical diagram",
     "ascii_sketch": "[MAIN COMPONENT]---[SUB COMPONENT]\n     |\n[CONNECTION POINT]"
   }'
   ```

### Tavily API Errors

**Error**: `401 Unauthorized` - Invalid or expired API key

**Error**: `Rate limit exceeded` - Wait 1-2 minutes before retrying

---

## Fetch Phase Errors

### All Image Fetches Failed

**Error**: `Failed to fetch any reference images`

**Resolution**:
1. Try different search terms to get images from different sources
2. Check ScrapeNinja status at RapidAPI dashboard
3. Provide ASCII sketch as generation guidance

### Partial Fetch Failures

**Warning**: `Failed to fetch [URL]: Connection timeout`

This is normal - script continues with successfully fetched images.

---

## Generation Phase Errors

### Gemini Generation Failed

**Error**: `400 Bad Request`

**Resolution**:
1. Simplify the prompt - fewer elements
2. Use fewer reference images (1-2 instead of 3)
3. Remove special characters from query

**Error**: `429 Rate Limit`

Wait 1-2 minutes, reduce count to 1.

### No Images Generated

**Error**: `Gemini generation returned no images`

**Resolution**:
1. Simplify requirements:
   ```bash
   --image-reference-query "[PRODUCT TYPE] product photo"
   --prompt-image-creation-needs '{"colors": ["#ffffff"], "style": "marketing shot"}'
   ```
2. Try different aspect ratio (1:1 or 4:3 are most reliable)

### Wrong Product Type Generated

**Symptom**: Generated image shows wrong product category.

**Resolution**:
1. Be more specific in query:
   - `"[BRAND] [MODEL] [PRODUCT TYPE] exploded view (NOT [WRONG TYPE])"`

2. Add exclusion terms:
   - `"[PRODUCT TYPE] NOT [VARIANT A] NOT [VARIANT B]"`

---

## Output Quality Issues

### Blurry or Low Quality Output

**Resolution**:
```json
{"detail": "2k"}
```
or
```json
{"detail": "4k"}
```

### Incorrect Colors

**Resolution**:
1. Verify hex format: `#dc2626` not `dc2626`
2. Order colors by importance - first is primary:
   ```json
   {"colors": ["#111827", "#dc2626", "#ffffff"]}
   ```
3. Use 2-3 colors, not many

### Text Appearing in Image

**Cause**: Reference images contain text, or labels were specified.

**Resolution**:
1. Omit `labels` field entirely for clean images
2. Use only the labels you want:
   ```json
   {"colors": ["#333333"], "style": "infographic", "labels": ["Feature 1", "Feature 2"]}
   ```
3. For text-free images:
   ```json
   {"colors": ["#333333"], "style": "marketing shot"}
   ```

### Composition Issues

**Resolution**:
1. Provide ASCII sketch:
   ```json
   {"colors": ["#333333"], "style": "infographic", "ascii_sketch": "[LEFT 60%: Product] | [RIGHT 40%: Features]"}
   ```
2. Reduce complexity - fewer features, single focal point

---

## Workflow Optimization

### Reducing API Costs
- Start with `"detail": "1k"` for drafts
- Use `"count": 1` until satisfied with prompt
- Reuse reference images for product variations

### Improving Consistency
- Save working prompt templates for product categories
- Document successful color palettes per brand
- Create ASCII sketch library for common layouts

### Speed Optimization
- Use specific searches to reduce irrelevant results
- Limit to 1-2 reference images
- Use 1k detail for iteration, upgrade for final

---

## Emergency Fallbacks

If complete workflow fails:

1. **Manual reference**: Download reference image manually, use ASCII sketch to describe it

2. **Text-only generation**: Skip search, provide detailed ASCII sketch

3. **Alternative approach**: Use Gemini directly via web interface
