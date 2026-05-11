[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE.md)

**🌐 语言：[中文](README.md) | [English](README_EN.md)**

---

# AI Vision Metadata CN

**版本：** 1.1.0  
**原作者：** RelUnrelated (<dan@relunrelated.com>)  
**中文增强版维护者：** liuzj288  
**许可证：** GNU 通用公共许可证 v3.0 (GPLv3) — 详见 `LICENSE.md` 文件。  
**更新日志：** 详见 `CHANGELOG.md` 文件了解版本发布历史和更新内容。  

---

## 概述
AI Vision Metadata CN 是 AI Vision Metadata Calibre 插件的中文增强分支，旨在自动从出版物封面中提取元数据。通过利用先进的 AI 视觉模型，它可以分析封面图像以识别具体的期号、出版日期、出版商和创作者，是目录化漫画、杂志和古董期刊的宝贵工具。

### 中文增强版 (v1.1.0) 新特性
- **OpenAI 兼容提供商**：通过可自定义的 Base URL 连接任何遵循 OpenAI API 规范的第三方服务（如 DeepSeek、Moonshot 等）。
- **中文默认提示词**：所有默认系统提示词现为中文，提供更好的本地化体验。
- **内容格式类型**：支持自动检测、图书、期刊杂志三种模式，每种模式都有优化的提示词和 JSON 模式。
- **增强的错误信息**：更友好的错误提示，特别是 OpenAI 兼容连接的错误信息。

## 核心功能

* **多提供商路由：** 无缝切换云端 AI 模型（Google Gemini、OpenAI、Anthropic、OpenAI 兼容），或通过 Ollama、LM Studio 将请求路由到本地离线模型。
* **OpenAI 兼容支持：** 通过配置自定义 Base URL 和 API 密钥，使用任何遵循 OpenAI API 标准的第三方 LLM 服务。
* **顺序批处理：** 可同时选择多本出版物。插件会在后台智能排队请求，避免速率限制和 UI 锁定。
* **并排审查界面：** 插件会将缩略图封面图像与提取的元数据并排展示，方便您轻松验证 AI 的准确性。
* **隔离的记忆存储：** 配置菜单安全地记住每个提供商各自的 API 密钥、模型选择和自定义系统提示词。
* **内容格式优化：** 针对图书和期刊杂志使用不同的提示词和 JSON 模式，以获得更准确的元数据提取效果。
* **中文本地化：** 默认提示词和 UI 元素针对中文用户进行了优化。
* **线程安全架构：** 后台处理确保主 Calibre 窗口永不冻结，同时优雅地捕获和报告网络或 API 错误。

## 安装方法
由于这是自定义插件，必须通过 Calibre 界面手动安装。

1. 下载发布归档文件，其中包含 `ai_vision_metadata.zip` 插件文件。*（请勿解压此插件文件）。*
2. 打开 Calibre，点击顶部工具栏中的**首选项**（齿轮图标）。
3. 在"高级"部分下，点击**插件**。
4. 点击右下角的**从文件加载插件**按钮。
5. 找到并选择 `ai_vision_metadata.zip` 文件。
6. 点击**是**接受安全警告并安装插件。
7. 重启 Calibre 使更改生效。

## 配置说明
使用前必须配置 API 密钥或本地服务器地址。

1. 进入 **首选项 > 插件**，在 *用户界面操作* 类别中找到 **AI Vision Metadata CN**，双击打开配置窗口。
2. **AI 提供商：** 从下拉菜单中选择您偏好的 AI 引擎：
   - Google Gemini
   - OpenAI
   - Anthropic
   - **OpenAI 兼容**（新功能）— 适用于任何遵循 OpenAI API 标准的第三方服务
   - 本地模型（Ollama/LM Studio）
3. **API 密钥 / 本地 URL：** 粘贴所选云提供商的 API 密钥。如使用本地模型，请确保本地 Base URL 正确。
4. **Base URL（OpenAI 兼容）：** 使用 OpenAI 兼容提供商时，输入服务的 Base URL（如 `https://api.deepseek.com/v1`）。默认值为 `https://api.openai.com/v1`。
5. **模型名称：** 点击**获取可用模型**从所选提供商直接填充下拉菜单，然后选择您要使用的具体模型。
6. **内容格式类型：** 选择合适的格式：
   - **自动检测（通用）：** 默认模式，适用于大多数出版物
   - **图书：** 针对图书优化（强调 ISBN、作者、出版商）
   - **期刊杂志：** 针对期刊优化（强调 ISSN、卷号、期号、编辑）
7. **系统提示词（高级）：** 您可以在此安全地调整 AI 的核心指令。每个提供商独立记住自己的提示词。默认提示词为中文。
8. 点击**应用**或**确定**保存。

## OpenAI 兼容提供商设置

OpenAI 兼容提供商允许您连接任何实现 OpenAI API 规范的第三方 LLM 服务。包括以下服务：

- **DeepSeek**（Base URL：`https://api.deepseek.com/v1`）
- **Moonshot AI**（Base URL：`https://api.moonshot.cn/v1`）
- **智谱 AI (GLM)**（Base URL：`https://open.bigmodel.cn/api/paas/v4`）
- **通义千问**（Base URL：`https://dashscope.aliyuncs.com/compatible-mode/v1`）
- **Silicon Flow**（Base URL：`https://api.siliconflow.cn/v1`）
- 任何其他 OpenAI API 兼容服务

### 设置步骤：
1. 从 AI 提供商下拉菜单中选择 **OpenAI 兼容**。
2. 输入服务的 API 密钥。
3. 输入服务的 **Base URL**（必须以 `/v1` 或等效路径结尾）。
4. 点击**获取可用模型**加载可用模型，或手动输入模型名称。
5. 可选地自定义系统提示词。
6. 点击**应用**或**确定**保存。

### OpenAI 兼容连接故障排除：
- 如果收到"连接失败"错误，请验证 Base URL 是否正确且包含正确的路径（如 `/v1`）。
- 确保服务支持视觉/图像输入（如果您正在分析封面图像）。
- 检查 API 密钥是否有足够的目标服务信用/配额。
- 错误信息中包含已配置的 Base URL，以帮助诊断连接问题。

## 使用方法

配置完成后，插件将无缝集成到您的标准 Calibre 工作流中。

1. **选择出版物：** 在 Calibre 库中选择一个或多个包含封面图像的条目。*（完全支持批处理）。*
2. **触发插件：** 点击主工具栏上的 AI Vision Metadata CN 按钮，或右键点击选中的书籍，从上下文菜单中选择它。
3. **等待处理：** 插件在安全的后台线程中运行，它会分析第一张图像并编译数据。
4. **审查数据：** 出现"审查 AI 元数据"窗口，左侧显示封面图像，右侧显示提取的数据。
   * **操作指示：** 每个字段都包含一个标注（如 *替换*、*合并*、*追加*），让您清楚勾选该框是否会覆盖现有 Calibre 数据或安全地追加。
   * **复选框：** 使用复选框选择要导入的确切字段。未勾选的字段将被忽略，保留现有 Calibre 数据库条目。
   * **可编辑下拉框：** 如*系列索引*等字段提供自动生成的格式，但您可以直接在框中手动输入以应对特殊情况。
5. **应用并自动推进：** 点击**确定**将勾选的元数据直接保存到 Calibre。如果选择了多本书，插件将无缝加载队列中的下一个封面并立即开始处理。

## 提供商设置指南

要使用此插件的云功能，您需要从所选提供商生成 API 密钥。请像对待密码一样保护这些密钥。

**Google Gemini（推荐免费套餐）**
* 访问 [Google AI Studio](https://aistudio.google.com/app/apikey) 生成免费 API 密钥。
* *限额说明：* `gemini-2.0-flash` 提供慷慨的每日免费配额。建议使用 `gemini-2.5-pro` 处理复杂封面和深度网络搜索，但需要在 Google Cloud 账户中添加计费配置以解除严格的速率限制。

**OpenAI (ChatGPT)**
* 访问 [OpenAI 平台](https://platform.openai.com/api-keys) 生成密钥。
* *要求：* OpenAI 不再提供免费 API 额度。您必须向开发者仪表板添加预付费额度（最低 $5）才能使 API 处理请求。

**Anthropic (Claude)**
* 访问 [Anthropic 控制台](https://console.anthropic.com/settings/keys) 生成密钥。
* *要求：* 与 OpenAI 类似，Anthropic 要求您在 API 请求获得授权前向账户充值预付费额度（否则会立即收到 HTTP 400 错误）。

**OpenAI 兼容（第三方服务）**
* 任何实现 OpenAI API 规范的服务均可使用。
* 在插件配置中输入服务的 Base URL 和 API 密钥。
* 详见上方[OpenAI 兼容提供商设置](#openai-兼容提供商设置)章节。

**本地模型（Ollama / LM Studio）**
* 您可以在自己的硬件上完全离线运行视觉模型（如 `llava`）。
* 下载 [Ollama](https://ollama.com/) 或 [LM Studio](https://lmstudio.ai/)。确保本地服务器正在运行，在插件设置中验证 Base URL，并获取您已下载的模型。

## 内容格式类型

插件支持三种内容格式类型，每种都有优化的提示词和 JSON 返回模式：

| 格式类型 | 使用场景 | 关键字段 |
|----------|----------|----------|
| 自动检测 | 通用出版物 | series, volume, issue_number, creators, ids |
| 图书 | 图书和小说 | series, title, creators, isbn, publisher |
| 期刊杂志 | 期刊和杂志 | series, volume, issue_number, issn, editors |

当设置为"自动检测"时，插件使用覆盖所有出版物类型的通用提示词。为获得更准确的结果，请选择与您收藏匹配的具体格式类型。