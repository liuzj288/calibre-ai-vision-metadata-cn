## [1.1.0] - 2026-05-10
_CN Enhanced Release by liuzj288_

### Added
- **OpenAI Compatible Provider**: New "OpenAI Compatible" provider option with customizable Base URL, allowing users to connect to any third-party service that follows the OpenAI API specification (e.g., DeepSeek, Moonshot, etc.)
- **Base URL Configuration**: Users can set a custom `base_url` for the OpenAI Compatible provider. Defaults to `https://api.openai.com/v1` when not specified
- **Content Format Type Selector**: New "Content Format Type" dropdown with three options:
  - Auto Detect (General): Default mode for general publications
  - Book: Optimized prompt and JSON schema for books (ISBN, author, publisher focus)
  - Magazine/Journal: Optimized prompt and JSON schema for periodicals (ISSN, volume, issue, editor focus)
- **Chinese Default Prompts**: All default system prompts are now in Chinese, with differentiated JSON return schemas for books vs. magazines
- **Model Fetching for OpenAI Compatible**: "Fetch Available Models" button now works with the OpenAI Compatible provider using the custom Base URL
- **Enhanced Error Messages**: OpenAI Compatible provider includes specific error messages referencing the configured Base URL for easier troubleshooting

### Changed
- Plugin renamed to **AI Vision Metadata CN** to distinguish from the original plugin
- Developer credits updated to include **liuzj288** alongside original author RelUnrelated
- Default prompts changed from English to Chinese across all providers
- Schema version bumped to 1.1 with automatic migration for existing users

## [1.0.0] - 2026-03-25
_Initial public release of AI Vision Metadata plugin_

## [0.9.0] - 2026-02-26
_Pre-release testing, architecture validation, and UI stabilization._