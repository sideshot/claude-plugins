# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "tavily-python",
#     "requests",
#     "google-genai",
#     "pillow",
#     "anthropic",
# ]
# ///
"""
Product Studio - AI-powered product image generation for e-commerce.

Workflow: Search → Reference → Brand → Create → Verify

Usage:
    uv run product_studio.py \
        --image-reference-query "Blum TANDEM drawer slide exploded view" \
        --prompt-image-creation-needs '{"colors": ["#dc2626"], "style": "technical diagram", ...}' \
        --extra-gen-parameters '{"ratio": "21:9", "detail": "1k", "count": 1}' \
        --output "assets/generated/"
"""

import argparse
import base64
import io
import json
import mimetypes
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Pre-flight check for imports
def check_dependencies() -> list[str]:
    """Check if all required dependencies are available."""
    missing = []
    try:
        from tavily import TavilyClient
    except ImportError:
        missing.append("tavily-python")
    try:
        import requests
    except ImportError:
        missing.append("requests")
    try:
        from google import genai
    except ImportError:
        missing.append("google-genai")
    try:
        from PIL import Image
    except ImportError:
        missing.append("pillow")
    try:
        import anthropic
    except ImportError:
        missing.append("anthropic")
    return missing


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
    score: float = 0.0


class ProductStudio:
    """Main class for product image generation workflow."""

    # Aspect ratio mappings
    ASPECT_RATIOS = {
        "1:1": "1K",
        "3:4": "1K",
        "4:3": "1K",
        "9:16": "1K",
        "16:9": "1K",
        "21:9": "1K",  # Will be handled as closest supported
    }

    # Detail level to size mapping
    DETAIL_SIZES = {
        "1k": "1K",
        "2k": "2K",
        "4k": "4K",
    }

    def __init__(self):
        self.tavily_key = os.environ.get("TAVILY_API_KEY")
        self.scrapeninja_key = os.environ.get("SCRAPENINJA_API_KEY")
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    def preflight_check(self, output_dir: str) -> tuple[bool, str]:
        """
        Validate all prerequisites before starting the workflow.

        Returns:
            Tuple of (success, error_message)
        """
        errors = []

        # Check environment variables
        if not self.tavily_key:
            errors.append("TAVILY_API_KEY environment variable not set. Get your key at https://tavily.com")
        if not self.scrapeninja_key:
            errors.append("SCRAPENINJA_API_KEY environment variable not set. Get your key at https://rapidapi.com/restyler/api/scrapeninja")
        if not self.gemini_key:
            errors.append("GEMINI_API_KEY environment variable not set. Get your key at https://aistudio.google.com/apikey")
        if not self.anthropic_key:
            errors.append("ANTHROPIC_API_KEY environment variable not set. Get your key at https://console.anthropic.com")

        # Check output directory
        output_path = Path(output_dir)
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            # Create refs subdirectory for reference images
            refs_path = output_path / ".refs"
            refs_path.mkdir(exist_ok=True)
        except PermissionError:
            errors.append(f"Cannot create output directory: {output_dir} (permission denied)")
        except Exception as e:
            errors.append(f"Cannot create output directory: {output_dir} ({e})")

        # Check dependencies
        missing_deps = check_dependencies()
        if missing_deps:
            errors.append(f"Missing Python dependencies: {', '.join(missing_deps)}. Run with 'uv run' to auto-install.")

        if errors:
            return False, "\n".join(f"- {e}" for e in errors)

        return True, ""

    def search_images(self, query: str) -> list[ImageCandidate]:
        """
        Step 1: Search for reference images using Tavily.

        Args:
            query: Search query for finding reference images

        Returns:
            List of ImageCandidate objects
        """
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
                candidates.append(ImageCandidate(
                    url=img,
                    description=None
                ))

        return candidates

    def fetch_image(self, image_url: str) -> Optional[bytes]:
        """
        Step 2a: Fetch a single image through ScrapeNinja proxy.

        Args:
            image_url: URL of the image to fetch

        Returns:
            Image bytes or None if fetch failed
        """
        import requests

        url = "https://scrapeninja.p.rapidapi.com/scrape"

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
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response_json = response.json()

            if "body" in response_json:
                image_base64 = response_json["body"]
                return base64.b64decode(image_base64)
            return None
        except Exception as e:
            print(f"Warning: Failed to fetch {image_url}: {e}", file=sys.stderr)
            return None

    def fetch_all_images(self, candidates: list[ImageCandidate]) -> list[ImageCandidate]:
        """
        Step 2: Fetch all candidate images.

        Args:
            candidates: List of ImageCandidate objects

        Returns:
            List of candidates with fetched image data
        """
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
        prompt_needs: dict[str, Any],
        max_images: int = 3
    ) -> list[ImageCandidate]:
        """
        Step 3: Use Claude Haiku to select the best reference images.

        Selection criteria:
        - Consensus: Similar images from multiple sources
        - Clarity: Simple, clean images preferred
        - Relevance: Matches the generation needs

        Args:
            candidates: List of fetched ImageCandidate objects
            prompt_needs: The prompt-image-creation-needs dict
            max_images: Maximum number of images to select

        Returns:
            List of selected ImageCandidate objects (1-3)
        """
        import anthropic

        if not candidates:
            return []

        if len(candidates) <= max_images:
            return candidates

        client = anthropic.Anthropic(api_key=self.anthropic_key)

        # Build the selection prompt
        description = prompt_needs.get("description", "product image")
        style = prompt_needs.get("style", "general")

        # Prepare image content for Claude
        content = []
        content.append({
            "type": "text",
            "text": f"""Select the {max_images} best reference images for generating a {style} image.

Target: {description}

Selection criteria (in order of importance):
1. CONSENSUS: If multiple images show the same/similar view, prefer those (indicates accuracy)
2. CLARITY: Prefer clean, simple images over cluttered screenshots or complex backgrounds
3. RELEVANCE: Image directly shows what we need to generate
4. QUALITY: Sufficient resolution and detail

For each candidate image below, I'll show you the image and its description (if available).
After reviewing all images, respond with ONLY a JSON array of the indices (0-based) of the best {max_images} images.

Example response: [0, 3, 5]
"""
        })

        # Add each candidate image (optimize for Haiku processing)
        valid_images = 0
        for i, candidate in enumerate(candidates):
            if candidate.image_data:
                # Optimize image for API processing (resize, convert to standard format)
                mime_type, optimized_data = self._optimize_image(candidate.image_data, max_dimension=1024)

                # Skip images that couldn't be processed (e.g., AVIF)
                if mime_type is None or optimized_data is None:
                    continue

                content.append({
                    "type": "text",
                    "text": f"\n--- Image {valid_images} ---\nDescription: {candidate.description or 'No description'}\n"
                })
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": base64.b64encode(optimized_data).decode()
                    }
                })
                valid_images += 1

        content.append({
            "type": "text",
            "text": f"\nRespond with ONLY a JSON array of the {max_images} best image indices:"
        })

        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=100,
                messages=[{"role": "user", "content": content}]
            )

            # Parse the response
            response_text = response.content[0].text.strip()

            # Extract JSON array from response
            import re
            match = re.search(r'\[[\d,\s]+\]', response_text)
            if match:
                indices = json.loads(match.group())
                selected = []
                for idx in indices[:max_images]:
                    if 0 <= idx < len(candidates):
                        selected.append(candidates[idx])
                return selected

        except Exception as e:
            print(f"Warning: Haiku selection failed ({e}), using first {max_images} images", file=sys.stderr)

        # Fallback: return first max_images
        return candidates[:max_images]

    def _detect_image_format(self, image_data: bytes) -> str:
        """
        Detect actual image format from file bytes (magic numbers).

        Returns:
            File extension including dot (e.g., ".jpg", ".png")
        """
        if len(image_data) < 12:
            return ".bin"

        # Check magic numbers
        if image_data[:3] == b'\xff\xd8\xff':
            return ".jpg"
        elif image_data[:8] == b'\x89PNG\r\n\x1a\n':
            return ".png"
        elif image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
            return ".webp"
        elif image_data[:4] == b'GIF8':
            return ".gif"
        elif image_data[4:12] == b'ftypavif' or image_data[4:12] == b'ftypavis':
            return ".avif"
        elif image_data[4:12] == b'ftypheic' or image_data[4:12] == b'ftypmif1':
            return ".heic"
        else:
            return ".bin"

    def _optimize_image(self, image_data: bytes, max_dimension: int = 3072) -> tuple[str, bytes]:
        """
        Optimize image for API processing.
        - Converts unsupported formats (AVIF, HEIC) to JPEG/PNG
        - Resizes if too large
        - Supported output: JPEG, PNG (compatible with Claude & Gemini)

        Args:
            image_data: Raw image bytes
            max_dimension: Maximum width or height

        Returns:
            Tuple of (mime_type, optimized_bytes)
        """
        from PIL import Image

        try:
            img = Image.open(io.BytesIO(image_data))
            width, height = img.size

            # Resize if needed
            if max(width, height) > max_dimension:
                scale = max_dimension / max(width, height)
                new_size = (int(width * scale), int(height * scale))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()

            # Always convert to JPEG or PNG (universally supported)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img.save(buffer, format="PNG", optimize=True)
                return "image/png", buffer.getvalue()
            else:
                img = img.convert("RGB")
                img.save(buffer, format="JPEG", quality=85)
                return "image/jpeg", buffer.getvalue()

        except Exception as e:
            # If PIL can't open (e.g., AVIF without pillow-avif-plugin), skip this image
            print(f"Warning: Image optimization failed ({e}), skipping", file=sys.stderr)
            return None, None

    def generate_image(
        self,
        reference_images: list[ImageCandidate],
        prompt_needs: dict[str, Any],
        gen_params: dict[str, Any],
        search_query: str = ""
    ) -> tuple[list[bytes], dict[str, int], str]:
        """
        Step 4: Generate the product image using Gemini.

        Args:
            reference_images: Selected reference ImageCandidate objects
            prompt_needs: Generation requirements (colors, style, etc.)
            gen_params: Extra generation parameters (ratio, detail, count)
            search_query: Original search query for context

        Returns:
            Tuple of (list of generated image bytes, token usage dict, text response)
        """
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.gemini_key)

        # Build the generation prompt - use search_query as the primary description
        colors = prompt_needs.get("colors", [])
        style = prompt_needs.get("style", "product image")
        ascii_sketch = prompt_needs.get("ascii_sketch", "")
        labels = prompt_needs.get("labels", [])  # Explicit labels for infographics

        # Build brand styling string
        brand_styling = []
        if colors:
            brand_styling.append(f"colors: {', '.join(colors)}")
        if style:
            brand_styling.append(f"style: {style}")
        brand_string = "; ".join(brand_styling) if brand_styling else "professional e-commerce"

        # Core prompt using search query as the description
        prompt_parts = [
            f"Create a {style} about {search_query} that fits the brand's styling guidelines of {brand_string}.",
            "",
            "CRITICAL: Match the EXACT product shown in the reference image.",
            "CRITICAL: Show only ONE set of the product components, not duplicates.",
        ]

        # Text/label handling: explicit labels for infographics, otherwise no text
        if labels:
            prompt_parts.append(f"IMPORTANT: Include ONLY these labels in the image: {', '.join(labels)}")
            prompt_parts.append("Do not include any other text besides these specified labels.")
        else:
            prompt_parts.append("IMPORTANT: Do not include any text in the image.")

        if ascii_sketch:
            prompt_parts.append(f"\nLayout guide:\n{ascii_sketch}")

        full_prompt = "\n".join(p for p in prompt_parts if p)

        # Build content with reference images
        parts = [types.Part.from_text(text=full_prompt)]

        for ref in reference_images:
            if ref.image_data:
                mime_type, optimized_data = self._optimize_image(ref.image_data)
                # Skip images that couldn't be processed
                if mime_type is None or optimized_data is None:
                    continue
                parts.append(types.Part.from_bytes(data=optimized_data, mime_type=mime_type))
                if ref.description:
                    parts.append(types.Part.from_text(text=f"Reference context: {ref.description}"))

        contents = [types.Content(role="user", parts=parts)]

        # Configure generation
        detail = gen_params.get("detail", "1k").lower()
        image_size = self.DETAIL_SIZES.get(detail, "1K")

        config = types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
            image_config=types.ImageConfig(
                image_size=image_size
            ),
        )

        # Generate
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

        # Extract token usage
        token_usage = {
            "input": 0,
            "output": 0,
            "total": 0
        }

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
        """
        Step 5: Save generated and reference images.

        Args:
            generated_images: List of generated image bytes
            reference_images: List of reference ImageCandidate objects
            output_dir: Output directory path

        Returns:
            Tuple of (list of generated file paths, list of reference file paths)
        """
        output_path = Path(output_dir)
        refs_path = output_path / ".refs"
        refs_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        generated_files = []
        for i, img_data in enumerate(generated_images):
            filename = f"product_{timestamp}_{i}.png"
            filepath = output_path / filename
            with open(filepath, "wb") as f:
                f.write(img_data)
            generated_files.append(str(filepath))

        ref_files = []
        for i, ref in enumerate(reference_images):
            if ref.image_data:
                # Detect actual image format from bytes, not URL
                ext = self._detect_image_format(ref.image_data)

                filename = f"ref_{timestamp}_{i}{ext}"
                filepath = refs_path / filename
                with open(filepath, "wb") as f:
                    f.write(ref.image_data)
                ref_files.append(str(filepath))

        return generated_files, ref_files

    def run(
        self,
        image_reference_query: str,
        prompt_needs: dict[str, Any],
        gen_params: dict[str, Any],
        output_dir: str
    ) -> GenerationResult:
        """
        Execute the complete image generation workflow.

        Args:
            image_reference_query: Search query for Tavily
            prompt_needs: Generation requirements
            gen_params: Extra generation parameters
            output_dir: Output directory

        Returns:
            GenerationResult with status and outputs
        """
        # Pre-flight check
        success, error_msg = self.preflight_check(output_dir)
        if not success:
            return GenerationResult(
                status="error",
                message=f"Pre-flight check failed:\n{error_msg}"
            )

        # Step 1: Search
        print("Step 1/5: Searching for reference images...", file=sys.stderr)
        try:
            candidates = self.search_images(image_reference_query)
            if not candidates:
                return GenerationResult(
                    status="error",
                    message=f"No reference images found for query: '{image_reference_query}'\n\nSuggestions:\n- Try broader search terms\n- Remove specific model numbers\n- Provide an ASCII sketch as alternative guidance"
                )
            print(f"  Found {len(candidates)} candidate images", file=sys.stderr)
        except Exception as e:
            return GenerationResult(
                status="error",
                message=f"Tavily search failed: {e}\n\nCheck your TAVILY_API_KEY and internet connection."
            )

        # Step 2: Fetch
        print("Step 2/5: Fetching reference images...", file=sys.stderr)
        try:
            fetched = self.fetch_all_images(candidates)
            if not fetched:
                return GenerationResult(
                    status="error",
                    message="Failed to fetch any reference images.\n\nThe images may be blocked or unavailable. Try:\n- Different search terms\n- Providing an ASCII sketch as guidance"
                )
            print(f"  Successfully fetched {len(fetched)} images", file=sys.stderr)
        except Exception as e:
            return GenerationResult(
                status="error",
                message=f"Image fetching failed: {e}"
            )

        # Step 3: Select
        print("Step 3/5: Selecting best reference images...", file=sys.stderr)
        try:
            selected = self.select_best_images(fetched, prompt_needs)
            print(f"  Selected {len(selected)} reference images", file=sys.stderr)
        except Exception as e:
            print(f"  Warning: Selection failed ({e}), using first 3", file=sys.stderr)
            selected = fetched[:3]

        # Step 4: Generate (use only first reference for cleaner output)
        print("Step 4/5: Generating product image...", file=sys.stderr)
        # Use only the best reference image for cleaner generation
        best_reference = selected[:1]  # Take only the first (best) reference
        try:
            generated_images, token_usage, text_response = self.generate_image(
                best_reference, prompt_needs, gen_params, search_query=image_reference_query
            )
            if not generated_images:
                return GenerationResult(
                    status="error",
                    message=f"Gemini generation returned no images.\n\nResponse: {text_response}\n\nTry:\n- Simplifying the prompt\n- Using different reference images"
                )
            print(f"  Generated {len(generated_images)} images", file=sys.stderr)
        except Exception as e:
            return GenerationResult(
                status="error",
                message=f"Gemini generation failed: {e}\n\nCheck your GEMINI_API_KEY and try again."
            )

        # Step 5: Save
        print("Step 5/5: Saving outputs...", file=sys.stderr)
        try:
            generated_files, ref_files = self.save_outputs(
                generated_images, selected, output_dir
            )
        except Exception as e:
            return GenerationResult(
                status="error",
                message=f"Failed to save outputs: {e}"
            )

        return GenerationResult(
            status="success",
            files=generated_files,
            reference_images=ref_files,
            token_usage=token_usage,
            message=f"Successfully generated {len(generated_files)} image(s). Reference images saved for debugging."
        )


def main():
    parser = argparse.ArgumentParser(
        description="Product Studio - AI-powered product image generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run product_studio.py \\
        --image-reference-query "Blum TANDEM drawer slide exploded view" \\
        --prompt-image-creation-needs '{"colors": ["#dc2626"], "style": "technical diagram"}' \\
        --output "assets/generated/"
        """
    )

    parser.add_argument(
        "--image-reference-query",
        required=True,
        help="Search query for finding reference images via Tavily"
    )

    parser.add_argument(
        "--prompt-image-creation-needs",
        required=True,
        help="JSON object with colors, style, approach, target_audience, ascii_sketch, description"
    )

    parser.add_argument(
        "--extra-gen-parameters",
        default="{}",
        help="JSON object with ratio, detail, count (optional)"
    )

    parser.add_argument(
        "--output",
        default="assets/generated/",
        help="Output directory for generated images (default: assets/generated/)"
    )

    args = parser.parse_args()

    # Parse JSON arguments
    try:
        prompt_needs = json.loads(args.prompt_image_creation_needs)
    except json.JSONDecodeError as e:
        result = GenerationResult(
            status="error",
            message=f"Invalid JSON in --prompt-image-creation-needs: {e}"
        )
        print(result.to_json())
        sys.exit(1)

    try:
        gen_params = json.loads(args.extra_gen_parameters)
    except json.JSONDecodeError as e:
        result = GenerationResult(
            status="error",
            message=f"Invalid JSON in --extra-gen-parameters: {e}"
        )
        print(result.to_json())
        sys.exit(1)

    # Run the workflow
    studio = ProductStudio()
    result = studio.run(
        image_reference_query=args.image_reference_query,
        prompt_needs=prompt_needs,
        gen_params=gen_params,
        output_dir=args.output
    )

    # Output result as JSON
    print(result.to_json())

    # Exit with appropriate code
    sys.exit(0 if result.status == "success" else 1)


if __name__ == "__main__":
    main()
