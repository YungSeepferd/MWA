"""
Templates package for MWA Core notifier system.
"""

from pathlib import Path

# Template directory
TEMPLATE_DIR = Path(__file__).parent

# Available templates
EMAIL_TEMPLATES = {
    'default': 'email_default.html',
    'listings': 'email_listings.html',
    'contacts': 'email_contacts.html',
    'alert': 'email_alert.html',
}

DISCORD_TEMPLATES = {
    'default': 'discord_default.md',
    'listings': 'discord_listings.md',
    'contacts': 'discord_contacts.md',
}

SLACK_TEMPLATES = {
    'default': 'slack_default.md',
    'listings': 'slack_listings.md',
    'contacts': 'slack_contacts.md',
}

def get_template_path(template_type: str, template_name: str) -> Path:
    """
    Get the path to a template file.
    
    Args:
        template_type: Type of template ('email', 'discord', 'slack')
        template_name: Name of the template
        
    Returns:
        Path to the template file
    """
    template_map = {
        'email': EMAIL_TEMPLATES,
        'discord': DISCORD_TEMPLATES,
        'slack': SLACK_TEMPLATES,
    }
    
    if template_type not in template_map:
        raise ValueError(f"Unknown template type: {template_type}")
    
    templates = template_map[template_type]
    if template_name not in templates:
        raise ValueError(f"Unknown template '{template_name}' for type '{template_type}'")
    
    return TEMPLATE_DIR / templates[template_name]

def list_templates() -> dict:
    """
    List all available templates.
    
    Returns:
        Dictionary of available templates by type
    """
    return {
        'email': list(EMAIL_TEMPLATES.keys()),
        'discord': list(DISCORD_TEMPLATES.keys()),
        'slack': list(SLACK_TEMPLATES.keys()),
    }