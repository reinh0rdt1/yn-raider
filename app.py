from flask import Flask, render_template, request, jsonify
import random
import time
import json
from base64 import b64encode
import threading
import re
import tls_client
import logging
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')

class State:
    def __init__(self):
        self.tokens = []
        self.valid_tokens = []
        self.proxies = []
        self.joiner_running = False
        self.leaver_running = False
        self.spammer_running = False
        self.checker_running = False
        self.joiner_results = []
        self.leaver_results = []
        self.spammer_results = []
        self.checker_results = []

state = State()
EMOJIS = ['😀', '😂', '😍', '😎', '🤓', '👍', '👀', '🚀']

class Raider:
    def __init__(self):
        self.cookies = self.get_discord_cookies()
        self.props = self.super_properties()

    def get_discord_cookies(self):
        return "locale=en-US"

    def super_properties(self):
        payload = {
            "os": "Windows",
            "browser": "Discord Client",
            "release_channel": "stable",
            "client_version": "1.0.9179",
            "os_version": "10.0.19045",
            "system_locale": "en",
            "browser_user_agent": self.get_random_user_agent(),
            "browser_version": "32.2.7",
            "client_build_number": 362392,
            "native_build_number": 57782,
            "client_event_source": None,
        }
        return b64encode(json.dumps(payload).encode()).decode()

    def get_random_user_agent(self):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        return random.choice(user_agents)

    def headers(self, token):
        return {
            "authority": "discord.com",
            "accept": "*/*",
            "accept-language": "en",
            "authorization": token,
            "cookie": self.cookies,
            "content-type": "application/json",
            "user-agent": self.get_random_user_agent(),
            "x-discord-locale": "en-US",
            "x-debug-options": "bugReporterEnabled",
            "x-super-properties": self.props,
        }

    def joiner(self, token, invite):
        session = tls_client.Session(client_identifier="chrome_128", random_tls_extension_order=True)
        session.timeout_seconds = 10
        proxy = random.choice(state.proxies) if state.proxies else None
        if proxy:
            session.proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        
        try:
            payload = {"session_id": uuid.uuid4().hex}
            logger.info(f"Joining with token: {token[:10]}..., invite: {invite}, payload: {json.dumps(payload)}")
            response = session.post(
                f"https://discord.com/api/v9/invites/{invite}",
                headers=self.headers(token),
                json=payload
            )
            logger.info(f"Joiner request for {token[:10]}...: Status {response.status_code}, Response: {response.text}")
            if response.status_code == 200:
                guild_name = response.json().get('guild', {}).get('name', 'Unknown')
                state.joiner_results.append({'token': token[:10] + '...', 'status': 'success', 'message': f"Joined {guild_name}"})
            elif response.status_code == 400:
                error_msg = response.json().get('message', 'Bad Request')
                logger.error(f"Bad request for {token[:10]}... with invite {invite}: {error_msg}, Full response: {response.text}")
                if 'captcha_key' in response.text:
                    logger.warning(f"\033[33mCAPTCHA DETECTED: {token[:10]}... (invite: {invite})\033[0m")
                    state.joiner_results.append({'token': token[:10] + '...', 'status': 'error', 'message': f"[CAPTCHA] {error_msg}", 'captcha': True})
                else:
                    state.joiner_results.append({'token': token[:10] + '...', 'status': 'error', 'message': error_msg})
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                logger.warning(f"Rate limited for {token[:10]}..., retrying after {retry_after}s")
                time.sleep(float(retry_after))
                self.joiner(token, invite)  # Retry
            elif response.status_code == 401:
                logger.error(f"Unauthorized for {token[:10]}...: Invalid token")
                state.joiner_results.append({'token': token[:10] + '...', 'status': 'error', 'message': 'Unauthorized: Invalid token'})
            else:
                error_msg = response.json().get('message', f'HTTP {response.status_code}')
                logger.error(f"Joiner error for {token[:10]}...: {error_msg}")
                state.joiner_results.append({'token': token[:10] + '...', 'status': 'error', 'message': error_msg})
        except Exception as e:
            logger.error(f"Joiner exception for {token[:10]}...: {str(e)}")
            state.joiner_results.append({'token': token[:10] + '...', 'status': 'error', 'message': str(e)})

    def leaver(self, token, guild):
        session = tls_client.Session(client_identifier="chrome_128", random_tls_extension_order=True)
        session.timeout_seconds = 10
        proxy = random.choice(state.proxies) if state.proxies else None
        if proxy:
            session.proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        
        try:
            payload = {"lurking": False}
            response = session.delete(
                f"https://discord.com/api/v9/users/@me/guilds/{guild}",
                headers=self.headers(token),
                json=payload
            )
            logger.info(f"Leaver request for {token[:10]}...: Status {response.status_code}")
            if response.status_code == 204:
                state.leaver_results.append({'token': token[:10] + '...', 'status': 'success', 'message': "Left server"})
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                logger.warning(f"Rate limited for {token[:10]}..., retrying after {retry_after}s")
                time.sleep(float(retry_after))
                self.leaver(token, guild)  # Retry
            else:
                error_msg = response.json().get('message', f'HTTP {response.status_code}')
                state.leaver_results.append({'token': token[:10] + '...', 'status': 'error', 'message': error_msg})
        except Exception as e:
            logger.error(f"Leaver failed for {token[:10]}...: {str(e)}")
            state.leaver_results.append({'token': token[:10] + '...', 'status': 'error', 'message': str(e)})

    def spammer(self, token, channel, message):
        session = tls_client.Session(client_identifier="chrome_128", random_tls_extension_order=True)
        session.timeout_seconds = 10
        proxy = random.choice(state.proxies) if state.proxies else None
        if proxy:
            session.proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        
        try:
            payload = {"content": message}
            response = session.post(
                f"https://discord.com/api/v9/channels/{channel}/messages",
                headers=self.headers(token),
                json=payload
            )
            logger.info(f"Spammer request for {token[:10]}...: Status {response.status_code}")
            if response.status_code == 200:
                state.spammer_results.append({'token': token[:10] + '...', 'status': 'success', 'message': "Message sent"})
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                logger.warning(f"Rate limited for {token[:10]}..., retrying after {retry_after}s")
                time.sleep(float(retry_after))
                self.spammer(token, channel, message)  # Retry
            else:
                error_msg = response.json().get('message', f'HTTP {response.status_code}')
                state.spammer_results.append({'token': token[:10] + '...', 'status': 'error', 'message': error_msg})
        except Exception as e:
            logger.error(f"Spammer failed for {token[:10]}...: {str(e)}")
            state.spammer_results.append({'token': token[:10] + '...', 'status': 'error', 'message': str(e)})

    def token_checker(self, token):
        session = tls_client.Session(client_identifier="chrome_128", random_tls_extension_order=True)
        session.timeout_seconds = 10
        proxy = random.choice(state.proxies) if state.proxies else None
        if proxy:
            session.proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        
        try:
            response = session.get(
                "https://discord.com/api/v9/users/@me/library",
                headers=self.headers(token)
            )
            logger.info(f"Checker request for {token[:10]}...: Status {response.status_code}")
            if response.status_code == 200:
                user_data = session.get("https://discord.com/api/v9/users/@me", headers=self.headers(token)).json()
                verified = user_data.get('verified', False)
                nitro = bool(user_data.get('premium_type'))
                state.checker_results.append({'token': token[:10] + '...', 'fullToken': token, 'status': 'success', 'message': f"Valid{' (Nitro)' if nitro else ''}{' (Unverified)' if not verified else ''}", 'nitro': nitro})
            elif response.status_code == 403:
                state.checker_results.append({'token': token[:10] + '...', 'fullToken': token, 'status': 'error', 'message': "Locked", 'nitro': False})
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                logger.warning(f"Rate limited for {token[:10]}..., retrying after {retry_after}s")
                time.sleep(float(retry_after))
                self.token_checker(token)  # Retry
            else:
                error_msg = response.json().get('message', f'HTTP {response.status_code}')
                state.checker_results.append({'token': token[:10] + '...', 'fullToken': token, 'status': 'error', 'message': error_msg, 'nitro': False})
        except Exception as e:
            logger.error(f"Checker failed for {token[:10]}...: {str(e)}")
            state.checker_results.append({'token': token[:10] + '...', 'fullToken': token, 'status': 'error', 'message': str(e), 'nitro': False})

raider = Raider()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/join', methods=['POST'])
def join():
    data = request.json
    state.tokens = data.get('tokens', [])
    invite = data.get('inviteCode', '')
    delay = float(data.get('delay', 1))
    max_joins = int(data.get('maxJoins', len(state.valid_tokens) if state.valid_tokens else len(state.tokens)))
    max_threads = int(data.get('maxThreads', 5))

    if not state.tokens or not invite:
        logger.error("Joiner: Missing tokens or invite code")
        return jsonify({'message': 'Tokens or invite code required', 'results': []}), 400
    if not state.valid_tokens:
        logger.error("Joiner: No valid tokens found")
        return jsonify({'message': 'No valid tokens found. Run Checker first.', 'results': []}), 400

    invite_code = re.sub(r"(https?://)?(www\.)?(discord\.(gg|com)/(invite/)?|\.gg/)", "", invite)
    state.joiner_running = True
    state.joiner_results = []
    logger.info(f"Joiner started with invite: {invite_code}, tokens: {len(state.valid_tokens)}")

    # 招待コードの事前検証
    sample_token = state.valid_tokens[0]
    session = tls_client.Session(client_identifier="chrome_128", random_tls_extension_order=True)
    response = session.get(f"https://discord.com/api/v9/invites/{invite_code}", headers=raider.headers(sample_token))
    if response.status_code != 200:
        error_msg = response.json().get('message', f'HTTP {response.status_code}')
        logger.error(f"Invalid invite code {invite_code}: {error_msg}")
        state.joiner_results.append({'token': 'N/A', 'status': 'error', 'message': f"Invalid invite: {error_msg}"})
        state.joiner_running = False
        return jsonify({'message': f"Invalid invite: {error_msg}", 'results': state.joiner_results}), 400

    def run_joiner():
        join_tokens = state.valid_tokens[:max_joins]
        threads = []
        for token in join_tokens:
            if not state.joiner_running:
                break
            thread = threading.Thread(target=raider.joiner, args=(token, invite_code))
            threads.append(thread)
            thread.start()
            time.sleep(delay / max_threads)
        for thread in threads:
            thread.join()
        state.joiner_running = False
        logger.info(f"Joiner completed: {len(state.joiner_results)} results")

    threading.Thread(target=run_joiner, daemon=True).start()
    return jsonify({'message': 'Joiner started', 'results': state.joiner_results})

@app.route('/leave', methods=['POST'])
def leave():
    data = request.json
    state.tokens = data.get('tokens', [])
    guild_id = data.get('serverId', '')
    delay = float(data.get('delay', 1))
    max_threads = int(data.get('maxThreads', 5))

    if not state.tokens or not guild_id:
        logger.error("Leaver: Missing tokens or guild ID")
        return jsonify({'message': 'Tokens or guild ID required', 'results': []}), 400
    if not state.valid_tokens:
        logger.error("Leaver: No valid tokens found")
        return jsonify({'message': 'No valid tokens found. Run Checker first.', 'results': []}), 400

    state.leaver_running = True
    state.leaver_results = []
    logger.info(f"Leaver started with guild: {guild_id}, tokens: {len(state.valid_tokens)}")

    def run_leaver():
        leave_tokens = state.valid_tokens[:]
        threads = []
        for token in leave_tokens:
            if not state.leaver_running:
                break
            thread = threading.Thread(target=raider.leaver, args=(token, guild_id))
            threads.append(thread)
            thread.start()
            time.sleep(delay / max_threads)
        for thread in threads:
            thread.join()
        state.leaver_running = False
        logger.info(f"Leaver completed: {len(state.leaver_results)} results")

    threading.Thread(target=run_leaver, daemon=True).start()
    return jsonify({'message': 'Leaver started', 'results': state.leaver_results})

@app.route('/spam', methods=['POST'])
def spam():
    data = request.json
    state.tokens = data.get('tokens', [])
    channel_id = data.get('channelId', '')
    message = data.get('message', '')
    delay = float(data.get('delay', 1))
    count = int(data.get('spamCount', 10))
    max_threads = int(data.get('maxThreads', 5))

    if not state.tokens or not channel_id or not message:
        logger.error("Spammer: Missing tokens, channel ID, or message")
        return jsonify({'message': 'Tokens, channel ID, or message required', 'results': []}), 400
    if not state.valid_tokens:
        logger.error("Spammer: No valid tokens found")
        return jsonify({'message': 'No valid tokens found. Run Checker first.', 'results': []}), 400

    state.spammer_running = True
    state.spammer_results = []
    logger.info(f"Spammer started with channel: {channel_id}, count: {count}, tokens: {len(state.valid_tokens)}")

    def run_spammer():
        spam_tokens = state.valid_tokens[:]
        for _ in range(count):
            if not state.spammer_running:
                break
            threads = []
            for token in spam_tokens:
                thread = threading.Thread(target=raider.spammer, args=(token, channel_id, message))
                threads.append(thread)
                thread.start()
                time.sleep(delay / max_threads)  # スレッド間隔を調整
            for thread in threads:
                thread.join()
            time.sleep(delay)  # 各スパムラウンド間の待機
        state.spammer_running = False
        logger.info(f"Spammer completed: {len(state.spammer_results)} results")

    threading.Thread(target=run_spammer, daemon=True).start()
    return jsonify({'message': 'Spammer started', 'results': state.spammer_results})

@app.route('/check', methods=['POST'])
def check():
    data = request.json
    state.tokens = data.get('tokens', [])
    max_threads = int(data.get('maxThreads', 5))

    if not state.tokens:
        logger.error("Checker: Tokens missing")
        return jsonify({'message': 'Tokens required', 'results': []}), 400

    state.checker_running = True
    state.checker_results = []
    state.valid_tokens = []
    logger.info(f"Checker started with {len(state.tokens)} tokens")

    def run_checker():
        threads = []
        for token in state.tokens:
            if not state.checker_running:
                break
            thread = threading.Thread(target=raider.token_checker, args=(token,))
            threads.append(thread)
            thread.start()
            time.sleep(0.1)
        for thread in threads:
            thread.join()
        state.valid_tokens.extend([r['fullToken'] for r in state.checker_results if r['status'] == 'success' and 'Unverified' not in r['message']])
        state.checker_running = False
        logger.info(f"Checker completed: {len(state.valid_tokens)} valid tokens")

    threading.Thread(target=run_checker, daemon=True).start()
    return jsonify({'message': 'Checker started', 'results': state.checker_results})

@app.route('/stop_joiner', methods=['POST'])
def stop_joiner():
    state.joiner_running = False
    logger.info("Joiner stopped by user")
    return jsonify({'message': 'Joiner stopped'})

@app.route('/stop_leaver', methods=['POST'])
def stop_leaver():
    state.leaver_running = False
    logger.info("Leaver stopped by user")
    return jsonify({'message': 'Leaver stopped'})

@app.route('/stop_spammer', methods=['POST'])
def stop_spammer():
    state.spammer_running = False
    logger.info("Spammer stopped by user")
    return jsonify({'message': 'Spammer stopped'})

@app.route('/check_status', methods=['GET'])
def check_status():
    return jsonify({
        'joiner_running': state.joiner_running,
        'joiner_results': state.joiner_results,
        'leaver_running': state.leaver_running,
        'leaver_results': state.leaver_results,
        'spammer_running': state.spammer_running,
        'spammer_results': state.spammer_results,
        'checker_running': state.checker_running,
        'checker_results': state.checker_results,
        'valid_tokens': len(state.valid_tokens)
    })

@app.route('/proxies', methods=['POST'])
def save_proxies():
    state.proxies = request.json.get('proxies', [])
    logger.info(f"Saved {len(state.proxies)} proxies")
    return jsonify({'message': f"Saved {len(state.proxies)} proxies"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)