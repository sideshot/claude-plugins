# Prompt Patterns for Product Image Generation

Templates organized by image type. Replace `[PLACEHOLDERS]` with actual values.

## Schema Reference

```json
{
  "colors": ["#hex1", "#hex2"],
  "style": "technical diagram | infographic | marketing shot | educational",
  "labels": ["Label 1", "Label 2"],
  "ascii_sketch": "optional layout guide"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `colors` | array | Yes | Hex color codes for brand consistency |
| `style` | string | Yes | Image type/style |
| `labels` | array | No | Text labels to include (omit for no text) |
| `ascii_sketch` | string | No | ASCII layout guide for composition |

**Important:** The search query (`--image-reference-query`) serves as the image description.

---

## Technical Diagrams

### Exploded View
```bash
--image-reference-query "[BRAND] [SERIES] [PRODUCT TYPE] exploded view components"
--prompt-image-creation-needs '{
  "colors": ["#333333", "#666666", "#f60000"],
  "style": "technical diagram",
  "labels": ["[Component A]", "[Component B]", "[Component C]"]
}'
```

### Assembly Diagram
```bash
--image-reference-query "[PRODUCT TYPE] installation step by step"
--prompt-image-creation-needs '{
  "colors": ["#2c3e50", "#3498db", "#e74c3c"],
  "style": "technical diagram",
  "labels": ["Step 1", "Step 2", "Step 3"]
}'
```

### Cross-Section View
```bash
--image-reference-query "[PRODUCT TYPE] mechanism internal cross section"
--prompt-image-creation-needs '{
  "colors": ["#1a1a1a", "#4a90d9", "#f5f5f5"],
  "style": "technical diagram"
}'
```
*No labels - clean technical illustration*

---

## Infographics

### Feature Comparison
```bash
--image-reference-query "[PRODUCT A] vs [PRODUCT B] comparison"
--prompt-image-creation-needs '{
  "colors": ["#00a651", "#ed1c24", "#333333"],
  "style": "infographic",
  "labels": ["[Product A]", "[Product B]", "[Feature 1]", "[Feature 2]"],
  "ascii_sketch": "[PRODUCT A]  |  [PRODUCT B]\n  ✓ Feature  |  ✓ Feature\n  ✓ Feature  |  ✗ Missing"
}'
```

### Specification Highlight
```bash
--image-reference-query "[BRAND] [MODEL] specifications"
--prompt-image-creation-needs '{
  "colors": ["#0066cc", "#ffffff", "#333333"],
  "style": "infographic",
  "labels": ["[Spec 1]", "[Spec 2]", "[Spec 3]", "[Spec 4]"],
  "ascii_sketch": "    [Spec 1]\n       \\\n[Spec 2]--[PRODUCT]--[Spec 3]\n       /\n    [Spec 4]"
}'
```

### Benefits Overview
```bash
--image-reference-query "[PRODUCT TYPE] benefits features"
--prompt-image-creation-needs '{
  "colors": ["#28a745", "#17a2b8", "#ffc107"],
  "style": "infographic",
  "labels": ["[Benefit 1]", "[Benefit 2]", "[Benefit 3]"]
}'
```

---

## Marketing Shots

### Lifestyle Context
```bash
--image-reference-query "[PRODUCT TYPE] installed in use"
--prompt-image-creation-needs '{
  "colors": ["#f5f0e8", "#8b7355", "#2c2c2c"],
  "style": "marketing shot"
}'
```
*No labels - clean lifestyle imagery*

### Beauty Shot
```bash
--image-reference-query "[BRAND] [PRODUCT] product photo studio"
--prompt-image-creation-needs '{
  "colors": ["#ffffff", "#e0e0e0", "#333333"],
  "style": "marketing shot"
}'
```

### Product in Use
```bash
--image-reference-query "[PRODUCT TYPE] operation demonstration"
--prompt-image-creation-needs '{
  "colors": ["#f8f9fa", "#6c757d", "#007bff"],
  "style": "marketing shot"
}'
```

---

## Educational Visuals

### Installation Guide
```bash
--image-reference-query "[PRODUCT TYPE] installation guide steps"
--prompt-image-creation-needs '{
  "colors": ["#343a40", "#28a745", "#ffc107"],
  "style": "educational",
  "labels": ["1. Prep", "2. Mount", "3. Attach", "4. Adjust"],
  "ascii_sketch": "[1: Prep] [2: Mount]\n[3: Attach] [4: Adjust]"
}'
```

### Troubleshooting Visual
```bash
--image-reference-query "[PRODUCT TYPE] alignment problem solution"
--prompt-image-creation-needs '{
  "colors": ["#dc3545", "#28a745", "#6c757d"],
  "style": "educational",
  "labels": ["Problem", "Solution"],
  "ascii_sketch": "[WRONG ✗]  →  [RIGHT ✓]"
}'
```

### Maintenance Guide
```bash
--image-reference-query "[PRODUCT TYPE] maintenance points"
--prompt-image-creation-needs '{
  "colors": ["#17a2b8", "#6c757d", "#ffffff"],
  "style": "educational",
  "labels": ["Clean", "Lubricate", "Check"]
}'
```

---

## ASCII Sketch Templates

### Two-Column Layout
```
[LEFT: 60%]              | [RIGHT: 40%]
Main product image       | Feature 1 with icon
Full size, hero shot     | Feature 2 with icon
                         | Feature 3 with icon
[BOTTOM BAR: Brand accent color strip]
```

### Grid Layout
```
[TITLE AREA - Brand color background]
[Product 1] [Product 2] [Product 3]
[Spec row]  [Spec row]  [Spec row]
[Footer with logo area]
```

### Radial Layout
```
        [Feature N]
           |
[Feature W]--[PRODUCT]--[Feature E]
           |
        [Feature S]
```

### Sequential Layout
```
[Step 1] → [Step 2] → [Step 3] → [Step 4]
  Base      Mount      Connect    Complete
```

### Comparison Layout
```
[Header: VS comparison]
+------------------+------------------+
| Option A         | Option B         |
| [Image]          | [Image]          |
| • Feature 1      | • Feature 1      |
| • Feature 2      | ✗ Missing        |
+------------------+------------------+
```

---

## Color Palette Recommendations

### Technical/Professional
- Primary: `#2c3e50` (dark slate)
- Secondary: `#3498db` (bright blue)
- Accent: `#e74c3c` (red for emphasis)

### Modern/Clean
- Primary: `#1a1a1a` (near black)
- Secondary: `#666666` (medium gray)
- Accent: `#0066cc` (blue)

### Warm/Inviting
- Primary: `#8b4513` (saddle brown)
- Secondary: `#d2691e` (chocolate)
- Accent: `#ffd700` (gold)

### Bold/Energetic
- Primary: `#ff6b35` (orange)
- Secondary: `#004e89` (navy)
- Accent: `#f7c59f` (peach)

---

## Best Practices

### Labels Usage
- **Omit `labels`** for clean product shots, beauty shots, lifestyle imagery
- **Use `labels`** for infographics, diagrams, and educational content
- Keep labels short (1-3 words)
- Match label count to layout complexity

### By Image Type

| Type | Labels? | ASCII Sketch? |
|------|---------|---------------|
| Technical diagram | Often | Sometimes |
| Infographic | Yes | Recommended |
| Marketing shot | Rarely | No |
| Educational | Yes | Recommended |

### Query Construction
The search query is your image description. Make it specific:
- ✅ `"[BRAND] [MODEL] [PRODUCT TYPE] exploded view components"`
- ❌ `"[PRODUCT TYPE]"`

Include:
- Brand and model when known
- View type (exploded, installed, comparison)
- Key components to show
