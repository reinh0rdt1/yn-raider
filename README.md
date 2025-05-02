# YN-RAIDER [WEB-UI VERSION] 🚀

A sleek, lightweight **Discord automation tool** powered by **Python** and **Flask**. Automate server joining, token management, message spamming, and more through an intuitive web interface. Built for developers and enthusiasts, YN-RAIDER is your go-to for Discord automation tasks! 🎉

![Discord Raider](https://img.shields.io/badge/Discord-Raider-blueviolet?style=flat-square)  
![Python](https://img.shields.io/badge/Python-3.8+-yellow?style=flat-square)  
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

> **⚠️ Disclaimer**: This tool is for **educational purposes only**. Use responsibly and in compliance with [Discord's Terms of Service](https://discord.com/terms). The author is not liable for misuse.

> 👥 **Get Support**: Join our community on [Discord](https://discord.gg/HemBmKMYKF)

---

## 📸 Showcase

![SHOWCASE](https://i.imgur.com/6SWNSo6.png)

---

## ✨ Features
- **Server Joiner**: Join Discord servers using multiple tokens with an invite link, enhanced with proxy rotation and up to 3 retries for CAPTCHA countermeasures.
- **Server Leaver**: Easily leave specific servers with token-based automation.
- **Message Spammer**: Send messages to channels with customizable delays, thread counts, and optional delay-free fast transmission (rate limit aware).
- **Token Checker**: Validate tokens, checking Nitro status, verification, and more.
- **Token Manager**: Manage token details (email, creation date, username, user ID, avatar, validation status, nitro status) in a table with modal import/export.
- **Proxy Support**: Select HTTP, HTTPS, SOCKS4, or SOCKS5 via a drop-down menu, with input format validation (e.g., `ip:port`, `user:pass@ip:port`).
- **Web Interface**: Control all features through a user-friendly browser UI with responsive design and animated modals.

---

---
## 📙Installation
Follow these steps to set up Discord Raider:

### 1. Clone the Repository
```bash
git clone https://github.com/reinh0rdt1/yn-raider.git
cd yn-raider
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the YN-RAIDER
```bash
run setup.bat
```
---




## 🛠️ Prerequisites
To get started, you'll need:

- **Python 3.8+**: [Download here](https://www.python.org/downloads/)
- **Git**: [Install Git](https://git-scm.com/downloads) (optional, for cloning)
- **Proxies** (optional): Prepare a list of proxies (HTTP, HTTPS, SOCKS4, or SOCKS5) for Joiner and other features.
---

## 📦 Installation
run setup.bat

---

# 🛠️ Troubleshooting
Tool Not Starting?
Ensure Python 3.8+ and dependencies (flask, tls_client) are installed. Run python --version and pip list to verify.
Check setup.bat logs for errors (Windows users).

Proxy Errors?
Verify proxy format (ip:port or user:pass@ip:port) in the Proxy Settings modal.

Test proxies independently to ensure they are functional.

Token Import Fails?
Ensure tokens are formatted correctly (one per line) in the Token Manager's import modal.
Check for invalid or expired tokens in the logs.

---

# 📚License
```bash
This project is licensed under the MIT License - see the LICENSE file for details.
```




# git clone
```bash
git clone https://github.com/reinh0rdt1/yn-raider.git
cd yn-raider
