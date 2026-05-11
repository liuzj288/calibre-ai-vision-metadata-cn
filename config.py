# __license__   = 'GPL v3'
# __copyright__ = '2026, RelUnrelated <dan@relunrelated.com>, liuzj288'
from calibre.utils.config import JSONConfig

prefs = JSONConfig('plugins/ai_vision_metadata')
CURRENT_SCHEMA_VERSION = 1.1

def migrate_config_if_required():
    # Fetch the version, default to 0.9 if it doesn't exist yet
    schema_version = prefs.get('schema_version', 0.9)
    
    if schema_version < 1.0:
        # If upgrading from the 0.9 beta, set the new version
        prefs['schema_version'] = 1.0
        schema_version = 1.0
    
    if schema_version < 1.1:
        # v1.1: Add OpenAI Compatible provider support
        # Set default base_url for OpenAI Compatible provider
        if 'base_url_openai_compat' not in prefs:
            prefs['base_url_openai_compat'] = 'https://api.openai.com/v1'
        if 'api_key_openai_compat' not in prefs:
            prefs['api_key_openai_compat'] = ''
        if 'model_openai_compat' not in prefs:
            prefs['model_openai_compat'] = 'gpt-4o'
        if 'prompt_openai_compat' not in prefs:
            prefs['prompt_openai_compat'] = ''
        # Set default format_type if not present
        if 'format_type' not in prefs:
            prefs['format_type'] = 'auto'
        prefs['schema_version'] = CURRENT_SCHEMA_VERSION

# Run this immediately when the file is loaded
migrate_config_if_required()
