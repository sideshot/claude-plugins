# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "tavily-python",
#     "requests",
#     "google-genai",
#     "pillow",
#     "anthropic",
#     "httpx[socks]",
# ]
# ///
"""
Product Studio - AI-powered product image generation for e-commerce.

Workflow: Search → Fetch → Select → Generate → Save

Usage:
    uv run --no-cache product_studio.py \
        --subject "[Brand] [Model] [product type] exploded view" \
        --style-instructions "Technical diagram, white background" \
        --resolution 2k \
        --aspect-ratio 21:9 \
        --output "assets/generated/"
"""

import argparse
import base64
import io
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class GenerationResult:
    """Result of the image generation workflow."""
    status: str  # "success" or "error"
    files: list[str] = field(default_factory=list)
    reference_images: list[str] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=dict)
    message: str = ""

    def to_json(self) -> str:
        return json.dumps({
            "status": self.status,
            "files": self.files,
            "reference_images": self.reference_images,
            "token_usage": self.token_usage,
            "message": self.message
        }, indent=2)


@dataclass
class ImageCandidate:
    """A candidate reference image from Tavily search."""
    url: str
    description: Optional[str]
    image_data: Optional[bytes] = None
    matched_details: Optional[str] = None  # Haiku's analysis of how image matches subject
    confidence_score: float = 0.0


class ProductStudio:
    """Main class for product image generation workflow."""

    VALID_RESOLUTIONS = {"1k", "2k", "4k"}
    VALID_ASPECT_RATIOS = {"1:1", "4:3", "3:4", "16:9", "9:16", "21:9", "3:2", "2:3"}

    def __init__(self, debug: bool = False):
        self.tavily_key = os.environ.get("TAVILY_API_KEY")
        self.scrapeninja_key = os.environ.get("SCRAPENINJA_API_KEY")
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        self.debug = debug

    def _debug_print(self, label: str, content: str):
        """Print debug info to stderr."""
        if self.debug:
            print(f"\n{'='*60}", file=sys.stderr)
            print(f"[DEBUG] {label}", file=sys.stderr)
            print(f"{'='*60}", file=sys.stderr)
            print(content, file=sys.stderr)
            print(f"{'='*60}\n", file=sys.stderr)

    def preflight_check(self, output_dir: str) -> tuple[bool, str]:
        """Validate all prerequisites before starting."""
        errors = []

        if not self.tavily_key:
            errors.append("TAVILY_API_KEY not set")
        if not self.scrapeninja_key:
            errors.append("SCRAPENINJA_API_KEY not set")
        if not self.gemini_key:
            errors.append("GEMINI_API_KEY not set")
        if not self.anthropic_key:
            errors.append("ANTHROPIC_API_KEY not set")

        output_path = Path(output_dir)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            (output_path / ".refs").mkdir(exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create output directory: {e}")

        if errors:
            return False, "\n".join(f"- {e}" for e in errors)
        return True, ""

    def search_images(self, query: str) -> list[ImageCandidate]:
        """Step 1: Search for reference images using Tavily."""
        from tavily import TavilyClient

        client = TavilyClient(api_key=self.tavily_key)
        response = client.search(
            query=query,
            include_images=True,
            include_image_descriptions=True,
            max_results=10
        )

        candidates = []
        for img in response.get("images", []):
            if isinstance(img, dict):
                candidates.append(ImageCandidate(
                    url=img.get("url", ""),
                    description=img.get("description")
                ))
            elif isinstance(img, str):
                candidates.append(ImageCandidate(url=img, description=None))

        return candidates

    def fetch_image(self, image_url: str) -> Optional[bytes]:
        """Fetch a single image through ScrapeNinja proxy."""
        import requests

        payload = {
            "url": image_url,
            "method": "GET",
            "retryNum": 1,
            "geo": "us"
        }
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": self.scrapeninja_key,
            "X-RapidAPI-Host": "scrapeninja.p.rapidapi.com"
        }

        try:
            response = requests.post(
                "https://scrapeninja.p.rapidapi.com/scrape",
                json=payload,
                headers=headers,
                timeout=30
            )
            response_json = response.json()
            if "body" in response_json:
                return base64.b64decode(response_json["body"])
        except Exception as e:
            print(f"Warning: Failed to fetch {image_url}: {e}", file=sys.stderr)
        return None

    def fetch_all_images(self, candidates: list[ImageCandidate]) -> list[ImageCandidate]:
        """Step 2: Fetch all candidate images."""
        fetched = []
        for candidate in candidates:
            if candidate.url:
                image_data = self.fetch_image(candidate.url)
                if image_data:
                    candidate.image_data = image_data
                    fetched.append(candidate)
        return fetched

    def select_best_images(
        self,
        candidates: list[ImageCandidate],
        subject: str,
        min_score: float = 7.0
    ) -> list[ImageCandidate]:
        """Step 3: Use Claude Haiku to score and analyze reference images."""
        import anthropic

        if not candidates:
            return []

        client = anthropic.Anthropic(api_key=self.anthropic_key)

        content = [{
            "type": "text",
            "text": f"""Analyze each image for how well it represents: {subject}

For EACH image, provide:
- confidence_score: 0-10 (how well it matches the subject)
- matched_details: what specific elements in the image match the subject

Respond with ONLY a JSON array:
[
  {{"index": 0, "confidence_score": 9, "matched_details": "Shows exploded view with labeled bracket, runner, and locking device"}},
  {{"index": 1, "confidence_score": 3, "matched_details": "Only shows packaging, not the actual product"}}
]
"""
        }]

        valid_indices = []
        for i, candidate in enumerate(candidates):
            if candidate.image_data:
                mime_type, optimized_data = self._optimize_image(candidate.image_data, max_dimension=1024)
                if mime_type is None:
                    continue

                content.append({
                    "type": "text",
                    "text": f"\n--- Image {len(valid_indices)} ---\nDescription: {candidate.description or 'None'}\n"
                })
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": base64.b64encode(optimized_data).decode()
                    }
                })
                valid_indices.append(i)

        content.append({
            "type": "text",
            "text": "\nRespond with ONLY the JSON array, no other text:"
        })

        # Debug: print prompt (text parts only)
        if self.debug:
            prompt_text = "\n".join(
                item["text"] for item in content if item["type"] == "text"
            )
            self._debug_print("HAIKU PROMPT", f"{prompt_text}\n\n[+ {len(valid_indices)} images]")

        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1000,
                messages=[{"role": "user", "content": content}]
            )

            response_text = response.content[0].text.strip()
            self._debug_print("HAIKU RESPONSE", response_text)
            
            # Extract JSON array from response
            import re
            match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if match:
                scores = json.loads(match.group())
                
                # Filter by min_score and attach details to candidates
                selected = []
                for item in scores:
                    idx = item.get("index", -1)
                    score = item.get("confidence_score", 0)
                    details = item.get("matched_details", "")
                    
                    if score >= min_score and 0 <= idx < len(valid_indices):
                        candidate = candidates[valid_indices[idx]]
                        candidate.confidence_score = score
                        candidate.matched_details = details
                        selected.append(candidate)
                        print(f"    Image {idx}: score={score}, {details[:60]}...", file=sys.stderr)
                
                # Sort by score descending
                selected.sort(key=lambda c: c.confidence_score, reverse=True)
                return selected
                
        except Exception as e:
            print(f"Warning: Selection failed ({e}), using first 3", file=sys.stderr)

        return candidates[:3]

    def _detect_image_format(self, image_data: bytes) -> str:
        """Detect image format from magic bytes."""
        if len(image_data) < 12:
            return ".bin"

        if image_data[:3] == b'\xff\xd8\xff':
            return ".jpg"
        elif image_data[:8] == b'\x89PNG\r\n\x1a\n':
            return ".png"
        elif image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
            return ".webp"
        elif image_data[:4] == b'GIF8':
            return ".gif"
        elif image_data[4:12] in (b'ftypavif', b'ftypavis'):
            return ".avif"
        elif image_data[4:12] in (b'ftypheic', b'ftypmif1'):
            return ".heic"
        return ".bin"

    def _optimize_image(self, image_data: bytes, max_dimension: int = 3072) -> tuple[Optional[str], Optional[bytes]]:
        """Optimize image for API processing."""
        from PIL import Image

        try:
            img = Image.open(io.BytesIO(image_data))
            width, height = img.size

            if max(width, height) > max_dimension:
                scale = max_dimension / max(width, height)
                img = img.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img.save(buffer, format="PNG", optimize=True)
                return "image/png", buffer.getvalue()
            else:
                img = img.convert("RGB")
                img.save(buffer, format="JPEG", quality=85)
                return "image/jpeg", buffer.getvalue()
        except Exception as e:
            print(f"Warning: Image optimization failed ({e})", file=sys.stderr)
            return None, None

    def generate_image(
        self,
        reference_images: list[ImageCandidate],
        subject: str,
        style_instructions: str,
        resolution: str,
        aspect_ratio: str
    ) -> tuple[list[bytes], dict[str, int], str]:
        """Step 4: Generate the product image using Gemini."""
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.gemini_key)

        parts = []
        
        # 1. Header Text
        parts.append(types.Part.from_text(text=f"TASK: Generate an image of `{subject}`.\n\nHere are the reference images:"))

        # 2. Images (Interleaved)
        for i, ref in enumerate(reference_images):
            if ref.image_data:
                mime_type, optimized_data = self._optimize_image(ref.image_data)
                if mime_type and optimized_data:
                    # Label
                    parts.append(types.Part.from_text(text=f"\n**Reference Image {i+1}:**"))
                    # Image
                    parts.append(types.Part.from_bytes(data=optimized_data, mime_type=mime_type))

        # 3. Instructions & Style (Final Text Block)
        style_line = f"\n\nApply styling: {style_instructions}" if style_instructions else ""
        
        final_instructions = f"""
INSTRUCTIONS:
1. First, analyze the reference image(s) above to identify the key product components, structure, and visual style.
   Note: Reference images may contain errors or be irrelevant. If a reference image clearly conflicts with the subject description or appears unrelated, ignore that specific image or element.
2. Second, understand the specific product details that make this item unique—accurate components matter.
3. Third, plan the composition and layout that best presents this subject.
4. Finally, generate the image combining accurate product details with professional presentation.{style_line}

Do not include the subject title text in the image unless explicitly requested."""

        parts.append(types.Part.from_text(text=final_instructions))

        contents = [types.Content(role="user", parts=parts)]

        # Map resolution to Gemini size
        size_map = {"1k": "1K", "2k": "2K", "4k": "4K"}
        image_size = size_map.get(resolution.lower(), "1K")

        config = types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=image_size
            ),
        )

        # Debug: print exact parts structure
        if self.debug:
            parts_debug = []
            for i, part in enumerate(parts):
                if hasattr(part, 'text') and part.text:
                    parts_debug.append(f"parts[{i}] = Part.from_text(text='''{part.text}''')")
                else:
                    parts_debug.append(f"parts[{i}] = Part.from_bytes(data=<image bytes>, mime_type='image/...')")
            
            self._debug_print("GEMINI PARTS STRUCTURE", "\n\n".join(parts_debug) + f"\n\n[config: aspect_ratio={aspect_ratio}, image_size={image_size}]")

        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=contents,
            config=config
        )

        generated_images = []
        text_response = ""

        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    generated_images.append(part.inline_data.data)
                if part.text:
                    text_response += part.text

        self._debug_print("GEMINI RESPONSE", f"Generated {len(generated_images)} image(s)\nText: {text_response or '(none)'}")

        token_usage = {"input": 0, "output": 0, "total": 0}
        if response.usage_metadata:
            token_usage["input"] = response.usage_metadata.prompt_token_count or 0
            token_usage["output"] = response.usage_metadata.candidates_token_count or 0
            token_usage["total"] = response.usage_metadata.total_token_count or 0

        return generated_images, token_usage, text_response

    def save_outputs(
        self,
        generated_images: list[bytes],
        reference_images: list[ImageCandidate],
        output_dir: str
    ) -> tuple[list[str], list[str]]:
        """Step 5: Save generated and reference images."""
        output_path = Path(output_dir)
        refs_path = output_path / ".refs"
        refs_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        generated_files = []
        for i, img_data in enumerate(generated_images):
            filepath = output_path / f"product_{timestamp}_{i}.png"
            filepath.write_bytes(img_data)
            generated_files.append(str(filepath))

        ref_files = []
        for i, ref in enumerate(reference_images):
            if ref.image_data:
                ext = self._detect_image_format(ref.image_data)
                filepath = refs_path / f"ref_{timestamp}_{i}{ext}"
                filepath.write_bytes(ref.image_data)
                ref_files.append(str(filepath))

        return generated_files, ref_files

    def run(
        self,
        subject: str,
        style_instructions: str,
        resolution: str,
        aspect_ratio: str,
        output_dir: str
    ) -> GenerationResult:
        """Execute the complete image generation workflow."""

        # Preflight
        success, error_msg = self.preflight_check(output_dir)
        if not success:
            return GenerationResult(status="error", message=f"Preflight failed:\n{error_msg}")

        # Step 1: Search
        print("Step 1/4: Searching for reference images...", file=sys.stderr)
        candidates = self.search_images(subject)
        if not candidates:
            return GenerationResult(
                status="error",
                message=f"No reference images found for: '{subject}'"
            )
        print(f"  Found {len(candidates)} candidates", file=sys.stderr)

        # Step 2: Fetch reference images
        print("Step 2/4: Fetching reference images...", file=sys.stderr)
        selected = []
        for candidate in candidates:
            if len(selected) >= 3:
                break
            
            image_data = self.fetch_image(candidate.url)
            if image_data:
                candidate.image_data = image_data
                selected.append(candidate)
                print(f"  Fetched image from {candidate.url}", file=sys.stderr)
        
        if not selected:
            return GenerationResult(
                status="error",
                message="Failed to fetch any reference images"
            )
        print(f"  Fetched {len(selected)} images", file=sys.stderr)

        # Step 4: Generate
        print("Step 3/4: Generating image...", file=sys.stderr)
        generated_images, token_usage, text_response = self.generate_image(
            selected,
            subject,
            style_instructions,
            resolution,
            aspect_ratio
        )
        if not generated_images:
            return GenerationResult(
                status="error",
                message=f"Gemini returned no images. Response: {text_response}"
            )
        print(f"  Generated {len(generated_images)} images", file=sys.stderr)

        # Step 5: Save
        print("Step 4/4: Saving outputs...", file=sys.stderr)
        generated_files, ref_files = self.save_outputs(generated_images, selected, output_dir)

        return GenerationResult(
            status="success",
            files=generated_files,
            reference_images=ref_files,
            token_usage=token_usage,
            message=f"Generated {len(generated_files)} image(s)"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Product Studio - AI-powered product image generation",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--subject",
        required=True,
        help="Product/component description for search and generation"
    )
    parser.add_argument(
        "--style-instructions",
        default="",
        help="Format and style directives"
    )
    parser.add_argument(
        "--resolution",
        default="1k",
        choices=["1k", "2k", "4k"],
        help="Output resolution (default: 1k)"
    )
    parser.add_argument(
        "--aspect-ratio",
        default="21:9",
        choices=["1:1", "4:3", "3:4", "16:9", "9:16", "21:9", "3:2", "2:3"],
        help="Output aspect ratio (default: 21:9)"
    )
    parser.add_argument(
        "--output",
        default="assets/generated/",
        help="Output directory (default: assets/generated/)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print prompts and responses for debugging"
    )

    args = parser.parse_args()

    studio = ProductStudio(debug=args.debug)
    result = studio.run(
        subject=args.subject,
        style_instructions=args.style_instructions,
        resolution=args.resolution,
        aspect_ratio=args.aspect_ratio,
        output_dir=args.output
    )

    print(result.to_json())
    sys.exit(0 if result.status == "success" else 1)


if __name__ == "__main__":
    main()
