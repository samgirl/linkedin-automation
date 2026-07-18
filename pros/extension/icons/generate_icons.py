"""Generate placeholder icons for Chrome extension."""

import base64
from pathlib import Path


def create_svg_icon(size: int) -> str:
    """Create a simple SVG icon."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <rect width="{size}" height="{size}" fill="#3B82F6" rx="4"/>
  <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="{size//3}" font-weight="bold" fill="white" text-anchor="middle" dy=".3em">P</text>
</svg>'''


def main():
    """Generate icons."""
    icons_dir = Path(__file__).parent
    
    sizes = [16, 48, 128]
    
    for size in sizes:
        svg_content = create_svg_icon(size)
        svg_file = icons_dir / f"icon{size}.svg"
        svg_file.write_text(svg_content)
        print(f"Created {svg_file}")
    
    # Also create a simple PNG placeholder
    # For production, use real PNG icons
    print("\nNote: For production, replace SVG icons with actual PNG files.")
    print("You can use tools like Figma or GIMP to create proper icons.")


if __name__ == "__main__":
    main()
