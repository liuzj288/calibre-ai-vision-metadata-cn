# __license__   = 'GPL v3'
# __copyright__ = '2026, RelUnrelated <dan@relunrelated.com>, liuzj288'
from calibre.customize import InterfaceActionBase

try:
    load_translations()
except NameError:
    pass

class AIVisionMetadataWrapper(InterfaceActionBase):
    name                    = 'AI Vision Metadata CN'
    description             = _('自动化出版物封面元数据提取（中文增强版）。支持Google Gemini、OpenAI、Anthropic、OpenAI兼容接口及本地离线模型。')
    supported_platforms     = ['windows', 'osx', 'linux']
    author                  = 'RelUnrelated, liuzj288'
    version                 = (1, 1, 0)
    minimum_calibre_version = (5, 0, 0)

    # THIS IS THE MAGIC STRING: 'folder_name.file_name:ClassName'
    actual_plugin           = 'calibre_plugins.ai_vision_metadata.main:AIVisionAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        if self.actual_plugin_:
            from calibre_plugins.ai_vision_metadata.main import ConfigWidget
            return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()