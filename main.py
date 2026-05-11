# __license__   = 'GPL v3'
# __copyright__ = '2026, RelUnrelated <dan@relunrelated.com>, liuzj288'
import base64
import json
import urllib.request
import datetime
import os
from qt.core import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                     QComboBox, QPushButton, QMessageBox, QIcon, QPixmap, 
                     pyqtSignal, Qt, QObject, QSpinBox, QMenu, QTextEdit)

from calibre.gui2 import error_dialog
from calibre.gui2.actions import InterfaceAction
from calibre.gui2.threaded_jobs import ThreadedJob
from calibre_plugins.ai_vision_metadata.config import prefs

try:
    load_translations()
except NameError:
    pass

class WorkerSignals(QObject):
    review_signal = pyqtSignal(object, object, object)
    error_signal = pyqtSignal(str)  

# --- 中文默认提示词模板（基于 Calibre 规定字段） ---

_PROMPT_ACCURACY_RULES = (
    "【准确性规则 - 严格遵守】：\n"
    "1. 只填写你能从封面上直接看到的信息。如果某项信息在封面上找不到，必须留空（字符串填''，数字填0，列表填[]）。\n"
    "2. 绝对不要猜测、编造或虚构任何信息，特别是 ISBN、ISSN、出版日期、期号等。\n"
    "3. 宁可留空也不要填写不确定的信息。\n\n"
)

_PROMPT_COMMON_HEADER = (
    "分析这本出版物的封面图片。\n"
    "第一步：判断它是【图书】还是【杂志/期刊/报纸】。\n"
    "判断依据：\n"
    "- 封面标注有 ISSN 号、期号（No./Issue/第X期）、卷号（Vol./第X卷）的 → 杂志/期刊/报纸\n"
    "- 封面标注有 ISBN 号、没有期号/卷号的 → 图书\n"
    "- 封面有漫画风格画面且有期号 → 漫画（comic）\n"
    "- 无法明确判断时，根据封面整体风格推断最可能的类型\n"
    "第二步：根据判断结果，仅返回该类型对应的 JSON 字段，不要返回其他类型的专用字段。\n"
)

_PROMPT_PUBLIC_FIELDS = (
    "【公共字段（所有出版物均需填写）】：\n"
    "'format_type'（字符串：必填，根据判断结果填写 'book'、'magazine'、'comic'、'newspaper'），\n"
    "'publisher'（字符串：封面上可见的出版公司或组织名称，看不到则填''），\n"
    "'creators'（字符串列表：见下方分类说明），\n"
    "'ids'（字符串：见下方分类说明），\n"
    "'comments'（字符串：仅基于封面可见文字和画面的简要2至3句描述，"
    "图书则简述主题；杂志则列出封面可见的文章标题或专题。不要编造内容），\n"
    "'tags'（字符串列表：基于封面可见内容的主题标签），\n"
    "'languages'（字符串列表：3位 ISO 639-2 语言代码。"
    "中文出版物使用 ['zho']，英文使用 ['eng']，根据封面文字判断）。\n"
)

_PROMPT_BOOK_FIELDS = (
    "【图书专用字段】（判断为图书时填写以下字段）：\n"
    "'title'（字符串：仅包含图书名称本身，如果有版本号应加上版本号，如XXX（第10版）），\n"
    "'series'（字符串：丛书名。仅当封面明确显示丛书信息时填写，否则填''），\n"
    "'volume'（字符串：封面有丛书编号才填，否则填''），\n"
    "'pub_year'（整数：封面上可见的出版年份，看不到填0），\n"
    "'pub_month'（整数：封面上可见的出版月份，看不到填0），\n"
    "'pub_day'（整数：封面上可见的出版日期，看不到填0），\n"
    "'creators'（字符串列表：封面上可见的作者/译者。如果是丛书只取本册主编。"
    "如果是译著，非中国原作者以中文规范译名优先，格式为'[国别简称] 中文规范译名'，"
    "将译者加入列表，放在原作者之后），\n"
    "'ids'（字符串：格式 'isbn:XXXXXXXXXX'。仅当封面上明确印刷了ISBN号时才填写，否则必须填''），\n"
)

_PROMPT_MAGAZINE_FIELDS = (
    "【杂志/期刊/报纸专用字段】（判断为杂志/期刊/报纸时填写以下字段）：\n"
    "'title'（字符串：严格按照 '[出版物名称], [日期], Volume [卷号], Issue [期号]' 格式。"
    "如果卷号或期号在封面上找不到，对应部分省略），\n"
    "'series'（字符串：杂志名称），\n"
    "'volume'（字符串：封面上可见的卷号，看不到填''），\n"
    "'issue_number'（字符串：封面上可见的期号，转换为阿拉伯数字，看不到填''），\n"
    "'pub_year'（整数：封面上可见的出版年份，看不到填0），\n"
    "'pub_month'（整数：封面上可见的出版月份，看不到填0），\n"
    "'pub_day'（整数：封面上可见的出版日期，看不到填0），\n"
    "'creators'（字符串列表：封面上可见的主编或编辑名称，看不到填空列表[]），\n"
    "'ids'（字符串：格式 'issn:XXXX-XXXX'。仅当封面上明确印刷了ISSN号时才填写，否则必须填''），\n"
)

_PROMPT_LANGUAGE_NOTE = (
    "\n重要提醒：\n"
    "1. 如果出版物是中文的，请使用简体中文返回 title、creators、comments 和 tags 字段的内容。\n"
    "2. 所有信息必须来自封面可见内容，绝对不要编造或猜测。\n"
    "3. 看不到的信息必须留空，不要试图补全。"
)

# 通用模式（自动判断图书/杂志）
DEFAULT_PROMPT_CN_AUTO = (
    _PROMPT_ACCURACY_RULES +
    _PROMPT_COMMON_HEADER +
    "请仅返回一个 JSON 对象。根据你判断的类型，返回对应类型的字段。\n\n" +
    _PROMPT_PUBLIC_FIELDS +
    "\n" + _PROMPT_BOOK_FIELDS +
    "\n" + _PROMPT_MAGAZINE_FIELDS +
    _PROMPT_LANGUAGE_NOTE
)

# 图书模式
DEFAULT_PROMPT_CN_BOOK = (
    _PROMPT_ACCURACY_RULES +
    "分析这本图书的封面，提取封面上可见的元数据信息。\n"
    "请仅返回一个包含以下键的 JSON 对象。\n\n" +
    _PROMPT_PUBLIC_FIELDS +
    _PROMPT_BOOK_FIELDS +
    _PROMPT_LANGUAGE_NOTE
)

# 期刊杂志模式
DEFAULT_PROMPT_CN_MAGAZINE = (
    _PROMPT_ACCURACY_RULES +
    "分析这本杂志/期刊的封面，提取封面上可见的元数据信息。\n"
    "请仅返回一个包含以下键的 JSON 对象。\n\n" +
    _PROMPT_PUBLIC_FIELDS +
    _PROMPT_MAGAZINE_FIELDS +
    _PROMPT_LANGUAGE_NOTE
)

# 兼容性：保留旧的英文默认提示词作为回退
DEFAULT_PROMPT = DEFAULT_PROMPT_CN_AUTO

def get_default_prompt_for_format(format_type='auto'):
    """根据格式类型返回对应的默认提示词"""
    if format_type == 'book':
        return DEFAULT_PROMPT_CN_BOOK
    elif format_type == 'magazine':
        return DEFAULT_PROMPT_CN_MAGAZINE
    else:
        return DEFAULT_PROMPT_CN_AUTO

def get_saved_prompt_for_provider(provider, format_type='auto'):
    """获取指定提供商和格式类型的保存提示词，如果没有保存则返回默认值"""
    key = 'prompt_{}'.format(provider.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_"))
    saved = prefs.get(key, '')
    if saved:
        return saved
    return get_default_prompt_for_format(format_type)

class ConfigWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)
        
        # --- 1. Provider Selection ---
        self.label_provider = QLabel(_('AI Provider:'))
        self.l.addWidget(self.label_provider)
        
        self.provider_combo = QComboBox(self)
        self.providers = ['Google Gemini', 'OpenAI', 'Anthropic', 'OpenAI Compatible', 'Local (Ollama/LM Studio)']
        self.provider_combo.addItems(self.providers)
        
        # --- Load saved provider, defaulting to Google ---
        saved_provider = prefs.get('ai_provider', 'Google Gemini')
        self.provider_combo.setCurrentText(saved_provider)
        self.provider_combo.currentIndexChanged.connect(self.toggle_provider_fields)
        self.l.addWidget(self.provider_combo)

        # --- Dynamic Helper Link Label ---
        self.link_label = QLabel()
        self.link_label.setOpenExternalLinks(True)
        self.l.addWidget(self.link_label)
        
        # --- 2. API Key Fields (Dedicated Memory Banks) ---
        self.label_key = QLabel(_('API Key:'))
        self.l.addWidget(self.label_key)
        
        # Google Key (Falls back to the old agnostic key so you don't lose it)
        self.key_google = QLineEdit(self)
        self.key_google.setText(prefs.get('api_key_google', prefs.get('api_key', '')))
        self.l.addWidget(self.key_google)
        
        # OpenAI Key
        self.key_openai = QLineEdit(self)
        self.key_openai.setText(prefs.get('api_key_openai', ''))
        self.l.addWidget(self.key_openai)
        
        # Anthropic Key
        self.key_anthropic = QLineEdit(self)
        self.key_anthropic.setText(prefs.get('api_key_anthropic', ''))
        self.l.addWidget(self.key_anthropic)
        
        # OpenAI Compatible Key
        self.key_openai_compat = QLineEdit(self)
        self.key_openai_compat.setText(prefs.get('api_key_openai_compat', ''))
        self.l.addWidget(self.key_openai_compat)
        
        # --- 3. Local Base URL Field ---
        self.label_url = QLabel(_('Local Base URL (e.g., http://localhost:11434):'))
        self.l.addWidget(self.label_url)
        self.url_input = QLineEdit(self)
        self.url_input.setText(prefs.get('local_url', 'http://localhost:11434'))
        self.l.addWidget(self.url_input)
        
        # --- 3b. OpenAI Compatible Base URL Field ---
        self.label_base_url = QLabel(_('Base URL (OpenAI Compatible):'))
        self.l.addWidget(self.label_base_url)
        self.base_url_input = QLineEdit(self)
        self.base_url_input.setText(prefs.get('base_url_openai_compat', 'https://api.openai.com/v1'))
        self.base_url_input.setPlaceholderText('https://api.openai.com/v1')
        self.l.addWidget(self.base_url_input)
        
        # --- 4. Model Selection Area (Dedicated Memory Banks) ---
        self.label_model = QLabel(_('Model Name:'))
        self.l.addWidget(self.label_model)
        self.model_layout = QHBoxLayout()
        
        # Google Model
        self.model_google = QComboBox(self)
        self.model_google.setEditable(True)
        saved_google = prefs.get('model_google', prefs.get('model_name', 'gemini-2.5-pro'))
        self.model_google.addItem(saved_google)
        self.model_google.setCurrentText(saved_google)
        self.model_layout.addWidget(self.model_google)
        
        # OpenAI Model
        self.model_openai = QComboBox(self)
        self.model_openai.setEditable(True)
        saved_openai = prefs.get('model_openai', 'gpt-4o')
        self.model_openai.addItem(saved_openai)
        self.model_openai.setCurrentText(saved_openai)
        self.model_layout.addWidget(self.model_openai)
        
        # Anthropic Model
        self.model_anthropic = QComboBox(self)
        self.model_anthropic.setEditable(True)
        saved_anthropic = prefs.get('model_anthropic', 'claude-3-7-sonnet-latest')
        self.model_anthropic.addItem(saved_anthropic)
        self.model_anthropic.setCurrentText(saved_anthropic)
        self.model_layout.addWidget(self.model_anthropic)
        
        # OpenAI Compatible Model
        self.model_openai_compat = QComboBox(self)
        self.model_openai_compat.setEditable(True)
        saved_openai_compat = prefs.get('model_openai_compat', 'gpt-4o')
        self.model_openai_compat.addItem(saved_openai_compat)
        self.model_openai_compat.setCurrentText(saved_openai_compat)
        self.model_layout.addWidget(self.model_openai_compat)
        
        # Local Model
        self.model_local = QComboBox(self)
        self.model_local.setEditable(True)
        saved_local = prefs.get('model_local', 'llava')
        self.model_local.addItem(saved_local)
        self.model_local.setCurrentText(saved_local)
        self.model_layout.addWidget(self.model_local)
        
        self.fetch_button = QPushButton(_("Fetch Available Models"), self)
        self.fetch_button.clicked.connect(self.fetch_models)
        self.model_layout.addWidget(self.fetch_button)
        
        self.l.addLayout(self.model_layout)

        # --- 5. Format Type Selection ---
        self.label_format = QLabel(_('Content Format Type:'))
        self.l.addWidget(self.label_format)
        
        self.format_combo = QComboBox(self)
        self.format_options = [
            ('auto', _('Auto Detect (General)')),
            ('book', _('Book')),
            ('magazine', _('Magazine/Journal'))
        ]
        for fmt_val, fmt_lbl in self.format_options:
            self.format_combo.addItem(fmt_lbl, fmt_val)
        
        saved_format = prefs.get('format_type', 'auto')
        for idx, (fmt_val, fmt_lbl) in enumerate(self.format_options):
            if fmt_val == saved_format:
                self.format_combo.setCurrentIndex(idx)
                break
        self.l.addWidget(self.format_combo)

        # --- 6. Timeout Configuration ---
        self.label_timeout = QLabel(_('Network Timeout (seconds):'))
        self.l.addWidget(self.label_timeout)
        
        self.timeout_spin = QSpinBox(self)
        self.timeout_spin.setRange(30, 86400) 
        self.timeout_spin.setValue(int(prefs.get('timeout', 300)))
        self.l.addWidget(self.timeout_spin)

        # --- 7. Prompt Tuning Area (Dedicated Memory Banks) ---
        self.prompt_layout = QHBoxLayout()
        self.label_prompt = QLabel(_('System Prompt (Advanced):'))
        
        self.reset_prompt_btn = QPushButton(_("Restore Default"), self)
        self.reset_prompt_btn.clicked.connect(self.restore_default_prompt)
        
        self.prompt_layout.addWidget(self.label_prompt)
        self.prompt_layout.addStretch()
        self.prompt_layout.addWidget(self.reset_prompt_btn)
        self.l.addLayout(self.prompt_layout)
        
        # Google Prompt
        self.prompt_google = QTextEdit(self)
        self.prompt_google.setAcceptRichText(False)
        self.prompt_google.setMinimumHeight(150)
        self.prompt_google.setPlainText(prefs.get('prompt_google', prefs.get('custom_prompt', DEFAULT_PROMPT_CN_AUTO)))
        self.l.addWidget(self.prompt_google)
        
        # OpenAI Prompt
        self.prompt_openai = QTextEdit(self)
        self.prompt_openai.setAcceptRichText(False)
        self.prompt_openai.setMinimumHeight(150)
        self.prompt_openai.setPlainText(prefs.get('prompt_openai', DEFAULT_PROMPT_CN_AUTO))
        self.l.addWidget(self.prompt_openai)
        
        # Anthropic Prompt
        self.prompt_anthropic = QTextEdit(self)
        self.prompt_anthropic.setAcceptRichText(False)
        self.prompt_anthropic.setMinimumHeight(150)
        self.prompt_anthropic.setPlainText(prefs.get('prompt_anthropic', DEFAULT_PROMPT_CN_AUTO))
        self.l.addWidget(self.prompt_anthropic)
        
        # OpenAI Compatible Prompt
        self.prompt_openai_compat = QTextEdit(self)
        self.prompt_openai_compat.setAcceptRichText(False)
        self.prompt_openai_compat.setMinimumHeight(150)
        self.prompt_openai_compat.setPlainText(prefs.get('prompt_openai_compat', DEFAULT_PROMPT_CN_AUTO))
        self.l.addWidget(self.prompt_openai_compat)
        
        # Local Prompt
        self.prompt_local = QTextEdit(self)
        self.prompt_local.setAcceptRichText(False)
        self.prompt_local.setMinimumHeight(150)
        self.prompt_local.setPlainText(prefs.get('prompt_local', DEFAULT_PROMPT_CN_AUTO))
        self.l.addWidget(self.prompt_local)

        # --- INITIALIZATION ---
        self.toggle_provider_fields()

    def toggle_provider_fields(self):
        """Dynamically shows/hides inputs based on the selected provider."""
        provider = self.provider_combo.currentText()
        
        # Hide all key inputs first
        self.key_google.setVisible(False)
        self.key_openai.setVisible(False)
        self.key_anthropic.setVisible(False)
        self.key_openai_compat.setVisible(False)
        # Hide all model combos first
        self.model_google.setVisible(False)
        self.model_openai.setVisible(False)
        self.model_anthropic.setVisible(False)
        self.model_openai_compat.setVisible(False)
        self.model_local.setVisible(False)        
        # Hide all prompt editing areas first
        self.prompt_google.setVisible(False)
        self.prompt_openai.setVisible(False)
        self.prompt_anthropic.setVisible(False)
        self.prompt_openai_compat.setVisible(False)
        self.prompt_local.setVisible(False)
        # Hide URL fields first
        self.label_url.setVisible(False)
        self.url_input.setVisible(False)
        self.label_base_url.setVisible(False)
        self.base_url_input.setVisible(False)
        
        if provider == 'Local (Ollama/LM Studio)':
            self.link_label.setText(_("Get Local Tools:") + ' <a href="https://ollama.com/download">Ollama</a> | <a href="https://lmstudio.ai/">LM Studio</a>')
            self.label_key.setVisible(False)
            self.label_url.setVisible(True)
            self.url_input.setVisible(True)
            self.model_local.setVisible(True)
            self.prompt_local.setVisible(True)
        elif provider == 'OpenAI Compatible':
            self.link_label.setText(_('Supports any OpenAI API compatible service (e.g., DeepSeek, Moonshot, etc.)'))
            self.label_key.setVisible(True)
            self.key_openai_compat.setVisible(True)
            self.label_base_url.setVisible(True)
            self.base_url_input.setVisible(True)
            self.model_openai_compat.setVisible(True)
            self.prompt_openai_compat.setVisible(True)
        else:
            self.label_key.setVisible(True)
            
            if provider == 'Google Gemini':
                self.link_label.setText('<a href="https://aistudio.google.com/app/apikey">' + _("Get Google API Key") + '</a>')
                self.key_google.setVisible(True)
                self.model_google.setVisible(True)
                self.prompt_google.setVisible(True)
            elif provider == 'OpenAI':
                self.link_label.setText('<a href="https://platform.openai.com/api-keys">' + _("Get OpenAI API Key") + '</a>')
                self.key_openai.setVisible(True)
                self.model_openai.setVisible(True)
                self.prompt_openai.setVisible(True)
            elif provider == 'Anthropic':
                self.link_label.setText('<a href="https://console.anthropic.com/settings/keys">' + _("Get Anthropic API Key") + '</a>')
                self.key_anthropic.setVisible(True)
                self.model_anthropic.setVisible(True)
                self.prompt_anthropic.setVisible(True)

    def fetch_models(self):
        provider = self.provider_combo.currentText()
        local_url = self.url_input.text().strip().rstrip('/')
        base_url = self.base_url_input.text().strip().rstrip('/')
        
        # --- 1. Identify the Active Key and Dropdown ---
        if provider == 'Google Gemini':
            api_key = self.key_google.text().strip()
            active_combo = self.model_google
        elif provider == 'OpenAI':
            api_key = self.key_openai.text().strip()
            active_combo = self.model_openai
        elif provider == 'Anthropic':
            api_key = self.key_anthropic.text().strip()
            active_combo = self.model_anthropic
        elif provider == 'OpenAI Compatible':
            api_key = self.key_openai_compat.text().strip()
            active_combo = self.model_openai_compat
        else:
            api_key = "" 
            active_combo = self.model_local
            
        # --- 2. Validation ---
        if provider not in ['Local (Ollama/LM Studio)'] and not api_key:
            QMessageBox.warning(self, _("Missing Key"), _("Please enter your API key for {0}.").format(provider))
            return
            
        if provider == 'Local (Ollama/LM Studio)' and not local_url:
            QMessageBox.warning(self, _("Missing URL"), _("Please enter your local server's Base URL."))
            return
            
        if provider == 'OpenAI Compatible' and not base_url:
            QMessageBox.warning(self, _("Missing Base URL"), _("Please enter the Base URL for the OpenAI Compatible service."))
            return
            
        # Clear ONLY the currently visible dropdown
        active_combo.clear()
        
        # --- 3. API Routing & Populating ---
        try:
            if provider == 'Google Gemini':
                url = "https://generativelanguage.googleapis.com/v1beta/models?key={}".format(api_key)
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))
                
                exclusion_list = ['gemini-2.0-flash', 'gemini-2.0-pro', 'gemini-1.0-pro']
                for model in data.get('models', []):
                    if 'generateContent' in model.get('supportedGenerationMethods', []):
                        model_id = model.get('name', '').replace('models/', '')
                        if model_id not in exclusion_list:
                            active_combo.addItem(model_id)
                            
            elif provider == 'OpenAI':
                url = "https://api.openai.com/v1/models"
                req = urllib.request.Request(url, headers={'Authorization': 'Bearer {}'.format(api_key)})
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))
                
                for model in data.get('data', []):
                    model_id = model.get('id', '')
                    if 'gpt-4o' in model_id or 'gpt-4-turbo' in model_id:
                        active_combo.addItem(model_id)
                        
            elif provider == 'Anthropic':
                anthropic_models = [
                    'claude-3-7-sonnet-latest',
                    'claude-3-5-sonnet-latest', 
                    'claude-3-5-haiku-latest',
                    'claude-3-opus-latest'
                ]
                active_combo.addItems(anthropic_models)
                
            elif provider == 'OpenAI Compatible':
                url = "{}/models".format(base_url)
                headers = {'Authorization': 'Bearer {}'.format(api_key)}
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))
                
                if 'data' in data:
                    for model in data.get('data', []):
                        active_combo.addItem(model.get('id', ''))
                elif isinstance(data, list):
                    for model in data:
                        if isinstance(model, dict):
                            active_combo.addItem(model.get('id', model.get('name', '')))
                        elif isinstance(model, str):
                            active_combo.addItem(model)
                            
            elif provider == 'Local (Ollama/LM Studio)':
                url = "{}/v1/models".format(local_url)
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=15) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    
                for model in data.get('data', []):
                    active_combo.addItem(model.get('id', ''))
                    
            QMessageBox.information(self, _("Success"), _("Models refreshed successfully!"))
            
        except Exception as e:
            QMessageBox.critical(self, _("Error"), _("Failed to fetch models: {0}").format(str(e)))

    def restore_default_prompt(self):
        reply = QMessageBox.question(self, _('Restore Default'), 
                                     _('Are you sure you want to overwrite your custom prompt with the default instructions?'),
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            provider = self.provider_combo.currentText()
            format_type = self.format_combo.currentData()
            default_prompt = get_default_prompt_for_format(format_type)
            
            if provider == 'Google Gemini':
                self.prompt_google.setPlainText(default_prompt)
            elif provider == 'OpenAI':
                self.prompt_openai.setPlainText(default_prompt)
            elif provider == 'Anthropic':
                self.prompt_anthropic.setPlainText(default_prompt)
            elif provider == 'OpenAI Compatible':
                self.prompt_openai_compat.setPlainText(default_prompt)
            elif provider == 'Local (Ollama/LM Studio)':
                self.prompt_local.setPlainText(default_prompt)

    def save_settings(self):
        # 1. Save the active provider
        prefs['ai_provider'] = self.provider_combo.currentText()
        
        # 2. Save API Keys & URLs
        prefs['api_key_google'] = self.key_google.text().strip()
        prefs['api_key_openai'] = self.key_openai.text().strip()
        prefs['api_key_anthropic'] = self.key_anthropic.text().strip()
        prefs['api_key_openai_compat'] = self.key_openai_compat.text().strip()
        prefs['local_url'] = self.url_input.text().strip()
        prefs['base_url_openai_compat'] = self.base_url_input.text().strip()
        
        # 3. Save Models
        prefs['model_google'] = self.model_google.currentText().strip()
        prefs['model_openai'] = self.model_openai.currentText().strip()
        prefs['model_anthropic'] = self.model_anthropic.currentText().strip()
        prefs['model_openai_compat'] = self.model_openai_compat.currentText().strip()
        prefs['model_local'] = self.model_local.currentText().strip()
        
        # 4. Save Custom Prompts
        prefs['prompt_google'] = self.prompt_google.toPlainText().strip()
        prefs['prompt_openai'] = self.prompt_openai.toPlainText().strip()
        prefs['prompt_anthropic'] = self.prompt_anthropic.toPlainText().strip()
        prefs['prompt_openai_compat'] = self.prompt_openai_compat.toPlainText().strip()
        prefs['prompt_local'] = self.prompt_local.toPlainText().strip()
        
        # 5. Save General Settings
        prefs['timeout'] = self.timeout_spin.value()
        prefs['format_type'] = self.format_combo.currentData()

class AIVisionAction(InterfaceAction):
    name = 'AI Vision Metadata CN' # DO NOT TRANSLATE
    action_spec = ('AI Vision Metadata CN', 'images/icon.png', _('Identify book via AI Vision (CN)'), 'Ctrl+Shift+I')

    def genesis(self):
        self.signals = WorkerSignals()
        self.signals.review_signal.connect(self._show_review_dialog, type=Qt.ConnectionType.QueuedConnection)
        self.signals.error_signal.connect(self._show_error_dialog, type=Qt.ConnectionType.QueuedConnection)

        self.qaction.triggered.connect(self.identify_book)
        
        self.menu = QMenu(self.gui)
        
        self.run_action = self.create_action(
            spec=(_('Identify Cover'), 'images/icon.png', _('Run AI Vision Metadata on selected book'), None),
            attr='run_action'
        )
        self.run_action.triggered.connect(self.identify_book)
        self.menu.addAction(self.run_action)
        
        self.menu.addSeparator()
        
        self.config_action = self.create_action(
            spec=('Configure AI Vision CN', 'images/config.png', 'Settings for AI Vision Metadata CN', None),
            attr='config_action'
        )
        self.config_action.triggered.connect(self.show_configuration)
        self.menu.addAction(self.config_action)
        
        self.qaction.setMenu(self.menu)
        
        try:
            resources = self.load_resources(['images/icon.png', 'images/config.png'])
            
            icon_data = resources.get('images/icon.png')
            if icon_data:
                pixmap = QPixmap()
                pixmap.loadFromData(icon_data)
                main_icon = QIcon(pixmap)
                self.qaction.setIcon(main_icon)
                self.run_action.setIcon(main_icon)
                
            config_data = resources.get('images/config.png')
            if config_data:
                config_pixmap = QPixmap()
                config_pixmap.loadFromData(config_data)
                self.config_action.setIcon(QIcon(config_pixmap))
                
        except Exception as e:
            pass

    def show_configuration(self):
        self.interface_action_base_plugin.do_user_config(self.gui)

    def identify_book(self):
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows or len(rows) == 0:
            from calibre.gui2 import error_dialog
            return error_dialog(self.gui, _('No Selection'), _('Please select at least one book.'), show=True)

        self.batch_queue = [self.gui.library_view.model().id(row) for row in rows]
        self.process_next_in_queue()

    def process_next_in_queue(self):
        if not hasattr(self, 'batch_queue') or not self.batch_queue:
            return

        book_id = self.batch_queue.pop(0)
        db = self.gui.current_db.new_api

        rel_path = db.field_for('path', book_id)
        if rel_path:
            lib_path = self.gui.current_db.library_path
            cover_path = os.path.join(lib_path, rel_path.replace('/', os.sep), 'cover.jpg')
        else:
            cover_path = None

        if not cover_path or not os.path.exists(cover_path):
            self.signals.error_signal.emit(_("Book ID {0} has no cover image to process. Skipping to next.").format(book_id))
            self.process_next_in_queue()
            return

        from calibre.gui2.threaded_jobs import ThreadedJob
        job = ThreadedJob(
            'identifying_book', 
            _('Analyzing cover for book ID: {0}').format(book_id),  
            self.run_api_request, 
            (book_id, cover_path, ""),
            {}, 
            self.job_finished
        )
        self.gui.job_manager.run_threaded_job(job)

    def run_api_request(self, book_id, cover_path, api_key_ignored, **kwargs):
        import time
        start_time = time.time()

        with open(cover_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode('utf-8')

        provider = prefs.get('ai_provider', 'Google Gemini')
        local_url = prefs.get('local_url', 'http://localhost:11434').rstrip('/')
        base_url_openai_compat = prefs.get('base_url_openai_compat', 'https://api.openai.com/v1').rstrip('/')
        format_type = prefs.get('format_type', 'auto')
        
        # --- Master Variable Router ---
        if provider == 'Google Gemini':
            api_key = prefs.get('api_key_google', prefs.get('api_key', ''))
            model_name = prefs.get('model_google', prefs.get('model_name', 'gemini-2.5-pro'))
            prompt = prefs.get('prompt_google', '') or get_default_prompt_for_format(format_type)
        elif provider == 'OpenAI':
            api_key = prefs.get('api_key_openai', '')
            model_name = prefs.get('model_openai', 'gpt-4o')
            prompt = prefs.get('prompt_openai', '') or get_default_prompt_for_format(format_type)
        elif provider == 'Anthropic':
            api_key = prefs.get('api_key_anthropic', '')
            model_name = prefs.get('model_anthropic', 'claude-3-7-sonnet-latest')
            prompt = prefs.get('prompt_anthropic', '') or get_default_prompt_for_format(format_type)
        elif provider == 'OpenAI Compatible':
            api_key = prefs.get('api_key_openai_compat', '')
            model_name = prefs.get('model_openai_compat', 'gpt-4o')
            prompt = prefs.get('prompt_openai_compat', '') or get_default_prompt_for_format(format_type)
        else:
            api_key = ""
            model_name = prefs.get('model_local', 'llava')
            prompt = prefs.get('prompt_local', '') or get_default_prompt_for_format(format_type)
            
        if not prompt: 
            prompt = get_default_prompt_for_format(format_type)

        # --- DYNAMIC ROUTING & PAYLOAD BUILDER ---
        headers = {'Content-Type': 'application/json'}

        if provider == 'Google Gemini':
            url = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}".format(model_name, api_key)
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/jpeg", "data": img_data}}
                    ]
                }],
                "tools": [{"googleSearch": {}}]
            }

        elif provider in ['OpenAI', 'OpenAI Compatible', 'Local (Ollama/LM Studio)']:
            if provider == 'OpenAI':
                url = "https://api.openai.com/v1/chat/completions"
                headers['Authorization'] = 'Bearer {}'.format(api_key)
            elif provider == 'OpenAI Compatible':
                url = "{}/chat/completions".format(base_url_openai_compat)
                headers['Authorization'] = 'Bearer {}'.format(api_key)
            else:
                url = "{}/v1/chat/completions".format(local_url)

            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,{}".format(img_data)}}
                        ]
                    }
                ],
                "response_format": {"type": "json_object"} 
            }

        elif provider == 'Anthropic':
            url = "https://api.anthropic.com/v1/messages"
            headers['x-api-key'] = api_key
            headers['anthropic-version'] = '2023-06-01'

            payload = {
                "model": model_name,
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": img_data
                                }
                            },
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
            }
        else:
             return {"error_msg": _("Unknown AI Provider selected.")}

        import urllib.error
        
        timeout_val = int(prefs.get('timeout', 300))
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')

            try:
                with urllib.request.urlopen(req, timeout=timeout_val) as response:
                    res_json = json.loads(response.read().decode('utf-8'))
                    
            except urllib.error.HTTPError as http_err:
                error_body = http_err.read().decode('utf-8')
                try:
                    error_json = json.loads(error_body)
                    clean_msg = error_json.get('error', {}).get('message', error_body)
                    return {"error_msg": _("{0} API Error ({1}): {2}").format(provider, http_err.code, clean_msg)}
                except json.JSONDecodeError:
                    return {"error_msg": _("{0} API Error (HTTP {1}): {2}").format(provider, http_err.code, error_body)}

            except TimeoutError:
                return {"error_msg": _("The AI took too long to analyze the cover. Please try again or increase the timeout.")}
            except urllib.error.URLError as url_err:
                if provider == 'OpenAI Compatible':
                    return {"error_msg": _("Connection failed to {0}: {1}\nPlease check your Base URL: {2}").format(provider, url_err.reason, base_url_openai_compat)}
                return {"error_msg": _("Network connection failed: {0}").format(url_err.reason)}
            except Exception as e:
                return {"error_msg": _("An unexpected error occurred: {0}").format(str(e))}
            
            # --- UNIFIED RESPONSE PARSER ---
            raw_text = ""
            
            if provider == 'Google Gemini':
                candidate = res_json.get('candidates', [{}])[0]
                if candidate.get('finishReason') == 'SAFETY':
                    return {"error_msg": _("The AI blocked this cover due to its safety filters.")}
                parts = candidate.get('content', {}).get('parts', [])
                if parts:
                    raw_text = parts[0].get('text', '')

            elif provider in ['OpenAI', 'OpenAI Compatible', 'Local (Ollama/LM Studio)']:
                choices = res_json.get('choices', [])
                if choices:
                    raw_text = choices[0].get('message', {}).get('content', '')

            elif provider == 'Anthropic':
                content_blocks = res_json.get('content', [])
                if content_blocks:
                    raw_text = content_blocks[0].get('text', '')

            if not raw_text:
                return {"error_msg": _("The AI returned an empty response. The model may have failed to process the image.")}
                
            # --- SURGICAL JSON EXTRACTION ---
            import re
            match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            
            if match:
                clean_json = match.group(0)
            else:
                clean_json = raw_text.replace('```json', '').replace('```', '').strip()
                
            try:
                metadata = json.loads(clean_json)
                
                elapsed = time.time() - start_time
                metadata['ai_provider'] = provider
                metadata['ai_model_used'] = model_name
                metadata['api_duration'] = round(elapsed, 1)
                
            except json.JSONDecodeError as e:
                return {"error_msg": _("Data Parsing Error: Could not read AI output.\nRaw Output: {0}...").format(raw_text[:150])}

            # --- ROMAN NUMERAL CONVERTER ---
            import re
            def convert_roman_to_arabic(val):
                if not val or not isinstance(val, str): return val
                val = val.strip().upper()
                if not re.match(r'^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$', val) or val == '':
                    return val 
                
                roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
                res = 0
                for i in range(len(val)):
                    if i > 0 and roman_map[val[i]] > roman_map[val[i - 1]]:
                        res += roman_map[val[i]] - 2 * roman_map[val[i - 1]]
                    else:
                        res += roman_map[val[i]]
                return str(res)
                
            if 'volume' in metadata:
                metadata['volume'] = convert_roman_to_arabic(str(metadata['volume']))
            if 'issue_number' in metadata:
                metadata['issue_number'] = convert_roman_to_arabic(str(metadata['issue_number']))
            
            try:
                dt = datetime.date(int(metadata['pub_year']), int(metadata['pub_month']), int(metadata['pub_day']))
                metadata['day_of_year'] = str(dt.timetuple().tm_yday)
            except:
                metadata['day_of_year'] = "1"
                
            return (book_id, metadata, cover_path)

        except Exception as e:
            return {"error_msg": _("Data Parsing Error: {0}").format(str(e))}

    def job_finished(self, job):
        if job.failed:
            return self.gui.job_exception(job, dialog_title=_("AI Vision Failed CN"))
            
        result = job.result
        
        if "error_msg" in result:
            self.signals.error_signal.emit(result["error_msg"])
            return
        else:
            book_id, metadata, cover_path = job.result
            self.signals.review_signal.emit(book_id, metadata, cover_path)
            
    def _show_review_dialog(self, book_id, metadata, cover_path):
        try:
            from calibre_plugins.ai_vision_metadata.ui import MetadataReviewDialog
            from calibre.gui2 import error_dialog
            
            d = MetadataReviewDialog(self.gui, metadata, cover_path)
            result = d.exec_()
            
            approved_data = d.get_approved_data() if result == d.Accepted else None
            
            d.setParent(None)
            d.deleteLater()
            
            if approved_data:
                self.apply_metadata(book_id, approved_data)
                
        except Exception as e:
            from calibre.gui2 import error_dialog
            error_dialog(self.gui, _('UI Error'), _('Could not launch review: {0}').format(str(e)), show=True)
            
        finally:
            self.process_next_in_queue()

    def _show_error_dialog(self, error_msg):
        from calibre.gui2 import error_dialog
        error_dialog(self.gui, _("AI Vision Error CN"), error_msg, show=True)

    def apply_metadata(self, book_id, approved_data):
        db = self.gui.current_db.new_api
        mi = db.get_metadata(book_id)
        
        if 'languages' in approved_data:
            langs = [l.strip().lower() for l in approved_data['languages'].split(',') if l.strip()]
            if langs:
                mi.languages = langs

        if 'title' in approved_data: 
            mi.title = approved_data['title']
            from calibre.ebooks.metadata import title_sort
            lang_code = mi.languages[0] if mi.languages else None
            mi.title_sort = title_sort(mi.title, lang=lang_code)
            
        if 'authors' in approved_data:
            authors = [a.strip() for a in approved_data['authors'].split(',') if a.strip()]
            if authors: 
                mi.authors = authors
                from calibre.ebooks.metadata import authors_to_sort_string
                mi.author_sort = authors_to_sort_string(mi.authors)
                
        if 'series' in approved_data: 
            mi.series = approved_data['series']
        if 'series_index' in approved_data:
            try: mi.series_index = float(approved_data['series_index'])
            except ValueError: pass

        if 'publisher' in approved_data:
            mi.publisher = approved_data['publisher']
            
        if 'pubdate' in approved_data:
            try:
                import datetime
                mi.pubdate = datetime.datetime.strptime(approved_data['pubdate'], "%Y-%m-%d")
            except ValueError:
                pass

        if 'tags' in approved_data:
            new_tags = [t.strip() for t in approved_data['tags'].split(',') if t.strip()]
            existing_tags = mi.tags if mi.tags else []
            for tag in new_tags:
                if tag not in existing_tags:
                    existing_tags.append(tag)
            mi.tags = existing_tags

        if 'identifiers' in approved_data:
            new_ids_str = approved_data['identifiers']
            existing_ids = mi.identifiers if mi.identifiers else {}
            for pair in new_ids_str.split(','):
                if ':' in pair:
                    key, val = pair.split(':', 1)
                    existing_ids[key.strip().lower()] = val.strip()
            mi.identifiers = existing_ids

        if 'comments' in approved_data:
            new_comments = approved_data['comments']
            existing_comments = mi.comments if mi.comments else ""
            if existing_comments.strip():
                mi.comments = "{}<br><br><b>AI Summary:</b><br>{}".format(existing_comments, new_comments)
            else:
                mi.comments = new_comments
                
        db.set_metadata(book_id, mi)
        self.gui.library_view.model().refresh_ids([book_id])