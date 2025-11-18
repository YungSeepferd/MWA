from jinja2 import Environment, FileSystemLoader, select_autoescape

from pathlib import Path

# Set up Jinja2 environment
TEMPLATES_DIR = Path(__file__).resolve().parent
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape()
)

def render_template(template_name: str, listing: dict, settings) -> str:
    """Render a Jinja2 template with listing data and settings."""
    template = env.get_template(template_name)
    return template.render(listing=listing, settings=settings)