[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE.md)

**🌐 Language: [English](README_EN.md) | [中文](README.md)**

---

# AI Vision Metadata CN

**Version:** 1.1.0  
**Original Author:** RelUnrelated (<dan@relunrelated.com>)  
**CN Enhanced by:** liuzj288  
**License:** GNU General Public License v3.0 (GPLv3) — See the `LICENSE.md` file for details.  
**Changelog:** See the `CHANGELOG.md` file for release history and updates.  

---

## Overview
AI Vision Metadata CN is a Chinese-enhanced fork of the AI Vision Metadata Calibre plugin, designed to automate the extraction of metadata from publication covers. By leveraging state-of-the-art AI vision models, it analyzes cover art to identify specific issue numbers, publication dates, publishers, and creators, making it an invaluable tool for cataloging comics, magazines, and vintage periodicals.

### What's New in CN Version (v1.1.0)
- **OpenAI Compatible Provider**: Connect to any third-party service that follows the OpenAI API specification (e.g., DeepSeek, Moonshot, etc.) with a customizable Base URL.
- **Chinese Default Prompts**: All default system prompts are now in Chinese for better localization.
- **Content Format Type**: Choose between Auto Detect, Book, or Magazine/Journal modes, each with optimized prompts and JSON schemas.
- **Enhanced Error Messages**: More helpful error messages, especially for OpenAI Compatible connections.

## Key Features

* **Multi-Provider Routing:** Seamlessly switch between cloud-based AI models (Google Gemini, OpenAI, Anthropic, OpenAI Compatible) or route requests to your own local, offline models using Ollama or LM Studio.
* **OpenAI Compatible Support:** Use any third-party LLM service that follows the OpenAI API standard by configuring a custom Base URL and API key.
* **Sequential Batch Processing:** Select multiple publications at once. The plugin intelligently queues the requests in the background, preventing rate-limit bans and UI lockups.
* **Side-by-Side Review GUI:** Never fly blind. The plugin presents a crisp, scaled thumbnail of the cover image right next to the extracted metadata, allowing you to easily verify the AI's accuracy.
* **Isolated Memory Banks:** The configuration menu securely remembers your distinct API keys, model selections, and custom system prompts for every individual provider.
* **Content Format Optimization:** Different prompts and JSON schemas for books vs. magazines/journals for more accurate metadata extraction.
* **Chinese Localization:** Default prompts and UI elements are optimized for Chinese users.
* **Thread-Safe Architecture:** Background processing ensures your main Calibre window never freezes, while gracefully catching and reporting network or API errors.

## Installation
Since this is a custom plugin, it must be installed manually through Calibre's interface.

1. Download the release archive. Inside, you will find the `ai_vision_metadata.zip` plugin file. *(Do not unzip this plugin file).*
2. Open Calibre and click on **Preferences** (the gear icon) in the top toolbar.
3. Under the "Advanced" section, click on **Plugins**.
4. Click the **Load plugin from file** button in the bottom right corner.
5. Navigate to and select the `ai_vision_metadata.zip` file.
6. Click **Yes** to accept the security warning and install the plugin.
7. Restart Calibre for the changes to take effect.

## Configuration
Before using the tool, you must configure it with an API key or a local server address.

1. Go to **Preferences > Plugins** and locate **AI Vision Metadata CN** under the *User interface action* category. Double-click to open the configuration window.
2. **AI Provider:** Select your preferred AI engine from the dropdown:
   - Google Gemini
   - OpenAI
   - Anthropic
   - **OpenAI Compatible** (NEW) — For any third-party service following the OpenAI API standard
   - Local (Ollama/LM Studio)
3. **API Key / Local URL:** Paste your API key for the selected cloud provider. If using a local model, ensure your Local Base URL is correct.
4. **Base URL (OpenAI Compatible):** When using the OpenAI Compatible provider, enter the Base URL of your service (e.g., `https://api.deepseek.com/v1`). Defaults to `https://api.openai.com/v1`.
5. **Model Name:** Click **Fetch Available Models** to populate the dropdown menu directly from your chosen provider, then select the specific model you wish to use.
6. **Content Format Type:** Choose the appropriate format:
   - **Auto Detect (General):** Default mode, works for most publications
   - **Book:** Optimized for books (emphasizes ISBN, author, publisher)
   - **Magazine/Journal:** Optimized for periodicals (emphasizes ISSN, volume, issue, editor)
7. **System Prompt (Advanced):** You can safely tweak the AI's core instructions here. Every provider remembers its own prompt. Default prompts are in Chinese.
8. Click **Apply** or **OK** to save.

## OpenAI Compatible Provider Setup

The OpenAI Compatible provider allows you to connect to any third-party LLM service that implements the OpenAI API specification. This includes services like:

- **DeepSeek** (Base URL: `https://api.deepseek.com/v1`)
- **Moonshot AI** (Base URL: `https://api.moonshot.cn/v1`)
- **Zhipu AI (GLM)** (Base URL: `https://open.bigmodel.cn/api/paas/v4`)
- **Qwen (Tongyi)** (Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`)
- **Silicon Flow** (Base URL: `https://api.siliconflow.cn/v1`)
- Any other OpenAI API compatible service

### Setup Steps:
1. Select **OpenAI Compatible** from the AI Provider dropdown.
2. Enter your API key for the service.
3. Enter the **Base URL** for the service (must end with `/v1` or equivalent).
4. Click **Fetch Available Models** to load available models, or manually enter the model name.
5. Optionally customize the system prompt.
6. Click **Apply** or **OK** to save.

### Troubleshooting OpenAI Compatible Connections:
- If you receive a "Connection failed" error, verify your Base URL is correct and includes the proper path (e.g., `/v1`).
- Ensure the service supports vision/image inputs if you're analyzing cover images.
- Check that your API key has sufficient credits/quota for the target service.
- The error message will include the configured Base URL to help diagnose connection issues.

## Usage
Once configured, the plugin integrates seamlessly into your standard Calibre workflow.

1. **Select Publications:** Highlight one or more entries in your Calibre library that have cover images. *(Batch processing is fully supported).*
2. **Trigger the Plugin:** Click the AI Vision Metadata CN button in your main toolbar, or right-click the highlighted books and select it from the context menu. 
3. **Wait for Processing:** The plugin runs in a safe background thread. It will analyze the first image and compile the data.
4. **Review the Data:** A "Review AI Metadata" window will appear, featuring the cover image on the left and the extracted data on the right. 
   * **Action Indicators:** Every field includes a muted sub-label (e.g., *Replaces*, *Merges*, *Appends*) so you know exactly whether checking the box will overwrite your existing Calibre data or safely add to it.
   * **Checkboxes:** Use the checkboxes to select exactly which fields you want to import. Unchecked fields will be ignored, preserving your existing Calibre database entries.
   * **Editable Dropdowns:** Fields like *Series Index* offer auto-generated formats, but you can manually type directly into the box for edge cases.
5. **Apply & Auto-Advance:** Click **OK** to save the checked metadata directly to Calibre. If you selected multiple books, the plugin will seamlessly load the next cover in your queue and begin processing it immediately.

## Provider Setup Guide

To use the cloud features of this plugin, you will need to generate an API key from your preferred provider. Treat these keys like passwords. 

**Google Gemini (Recommended for Free Tier)**
* Navigate to [Google AI Studio](https://aistudio.google.com/app/apikey) to generate a free API key.
* *Note on Limits:* `gemini-2.0-flash` offers generous free daily quotas. Using `gemini-2.5-pro` for complex covers and deep web searching is highly recommended, but it requires adding a billing profile to your Google Cloud account to lift strict rate limits.

**OpenAI (ChatGPT)**
* Navigate to the [OpenAI Platform](https://platform.openai.com/api-keys) to generate a key.
* *Requirements:* OpenAI no longer offers free API grants. You must add prepaid credits (minimum $5) to your developer dashboard for the API to process requests.

**Anthropic (Claude)**
* Navigate to the [Anthropic Console](https://console.anthropic.com/settings/keys) to generate a key.
* *Requirements:* Like OpenAI, Anthropic requires you to load prepaid credits to your account before API requests will be authorized (otherwise you will receive an immediate HTTP 400 error).

**OpenAI Compatible (Third-Party Services)**
* Any service that implements the OpenAI API specification can be used.
* Enter the service's Base URL and API key in the plugin configuration.
* See the [OpenAI Compatible Provider Setup](#openai-compatible-provider-setup) section above for details.

**Local Models (Ollama / LM Studio)**
* You can run vision-capable models (like `llava`) completely offline on your own hardware.
* Download [Ollama](https://ollama.com/) or [LM Studio](https://lmstudio.ai/). Make sure your local server is running, verify the Base URL in the plugin settings, and fetch the models you have downloaded.

## Content Format Types

The plugin supports three content format types, each with optimized prompts and JSON return schemas:

| Format Type | Use Case | Key Fields |
|-------------|----------|------------|
| Auto Detect | General publications | series, volume, issue_number, creators, ids |
| Book | Books and novels | series, title, creators, isbn, publisher |
| Magazine/Journal | Periodicals and magazines | series, volume, issue_number, issn, editors |

When set to "Auto Detect", the plugin uses a general-purpose prompt that covers all publication types. For more accurate results, select the specific format type that matches your collection.