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
import os
import string

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

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
]

class Raider:
    def __init__(self):
        self.cookies = self.get_discord_cookies()

    def get_discord_cookies(self):
        return "locale=en-US"

    def super_properties(self):
        os_options = ["Windows", "Mac OS X", "Linux", "iOS"]
        browsers = ["Chrome", "Firefox", "Safari", "Discord Client"]
        payload = {
            "os": random.choice(os_options),
            "browser": random.choice(browsers),
            "release_channel": "stable",
            "client_version": f"1.0.{random.randint(9000, 9999)}",
            "os_version": f"{random.randint(10, 14)}.{random.randint(0, 5)}.{random.randint(0, 9999)}",
            "system_locale": "en",
            "browser_user_agent": random.choice(USER_AGENTS),
            "browser_version": f"{random.randint(90, 120)}.{random.randint(0, 5)}.{random.randint(0, 999)}",
            "client_build_number": random.randint(350000, 400000),
            "native_build_number": random.randint(50000, 60000),
            "client_event_source": None,
        }
        return b64encode(json.dumps(payload).encode()).decode()

    def headers(self, token):
        return {
            "authority": "discord.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": token,
            "cookie": self.cookies,
            "content-type": "application/json",
            "user-agent": random.choice(USER_AGENTS),
            "x-discord-locale": "en-US",
            "x-debug-options": "bugReporterEnabled",
            "x-super-properties": self.super_properties(),
            "origin": "https://discord.com",
            "referer": "https://discord.com/channels/@me",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }

    def joiner(self, token, invite, proxy=None):
        session = tls_client.Session(client_identifier=f"chrome_{random.randint(120, 128)}", random_tls_extension_order=True)
        session.timeout_seconds = 15

        if not proxy and state.proxies:
            proxy = random.choice(state.proxies)
        if proxy:
            session.proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        else:
            logger.warning(f"No proxy available for token {token[:10]}...")

        try:
            invite_code = re.sub(r"(https?://)?(www\.)?(discord\.(gg|com)/(invite/)?|\.gg/)", "", invite)
            url = f"https://discord.com/api/v9/invites/{invite_code}"
            nonce = str(uuid.uuid4().int)
            payload = {
                "session_id": str(uuid.uuid4()),
                "nonce": nonce
            }

            logger.info(f"Joining with token: {token[:10]}..., invite: {invite_code}, proxy: {proxy}")

            info_response = session.get(url, headers=self.headers(token))
            if info_response.status_code != 200:
                logger.error(f"Failed to get invite info: {info_response.status_code}, {info_response.text}")
                state.joiner_results.append({'token': token[:10] + '...', 'status': 'error', 'message': f"Invalid invite: {info_response.text}"})
                return

            time.sleep(random.uniform(1, 3))

            response = session.post(url, headers=self.headers(token), json=payload)
            logger.info(f"Joiner response for {token[:10]}...: Status {response.status_code}, Response: {response.text[:100]}...")

            if response.status_code == 200:
                response_data = response.json()
                guild_name = response_data.get('guild', {}).get('name', 'Unknown')
                result = {'token': token[:10] + '...', 'status': 'success', 'message': f"Joined {guild_name}"}
                state.joiner_results.append(result)
                logger.info(f"{result['token']}: {result['message']}")
            elif response.status_code == 400:
                error_msg = response.json().get('message', 'Bad Request')
                if 'captcha_key' in response.text:
                    logger.warning(f"Captcha required for {token[:10]}... with proxy {proxy}")
                    if state.proxies and len(state.proxies) > 1:
                        new_proxy = random.choice([p for p in state.proxies if p != proxy])
                        logger.info(f"Retrying with new proxy: {new_proxy}")
                        time.sleep(random.uniform(5, 10))
                        self.joiner(token, invite, new_proxy)
                    else:
                        result = {'token': token[:10] + '...', 'status': 'error', 'message': "CAPTCHA required - no alternative proxy available"}
                        state.joiner_results.append(result)
                        logger.error(f"{result['token']}: {result['message']}")
                else:
                    result = {'token': token[:10] + '...', 'status': 'error', 'message': error_msg}
                    state.joiner_results.append(result)
                    logger.error(f"{result['token']}: {result['message']}")
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', random.uniform(5, 10))
                logger.warning(f"Rate limited for {token[:10]}..., retrying after {retry_after}s")
                time.sleep(float(retry_after))
                self.joiner(token, invite, proxy)
            elif response.status_code == 401:
                result = {'token': token[:10] + '...', 'status': 'error', 'message': 'Unauthorized: Invalid token'}
                state.joiner_results.append(result)
                logger.error(f"{result['token']}: {result['message']}")
            else:
                error_msg = response.json().get('message', f'HTTP {response.status_code}')
                result = {'token': token[:10] + '...', 'status': 'error', 'message': error_msg}
                state.joiner_results.append(result)
                logger.error(f"{result['token']}: {result['message']}")
        except Exception as e:
            result = {'token': token[:10] + '...', 'status': 'error', 'message': str(e)}
            state.joiner_results.append(result)
            logger.error(f"{result['token']}: {result['message']}")

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
                self.leaver(token, guild)
            else:
                error_msg = response.json().get('message', f'HTTP {response.status_code}')
                state.leaver_results.append({'token': token[:10] + '...', 'status': 'error', 'message': error_msg})
        except Exception as e:
            logger.error(f"Leaver failed for {token[:10]}...: {str(e)}")
            state.leaver_results.append({'token': token[:10] + '...', 'status': 'error', 'message': str(e)})

    def spammer(self, token, channel, message, random_emojis=False, random_strings=False):
        session = tls_client.Session(client_identifier="chrome_128", random_tls_extension_order=True)
        session.timeout_seconds = 10
        proxy = random.choice(state.proxies) if state.proxies else None
        if proxy:
            session.proxies = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}

        current_message = message
        if random_emojis and "{emoji}" not in current_message:
            current_message += " {emoji}"
        if random_strings and "{random_string}" not in current_message:
            current_message += " {random_string}"

        if "{emoji}" in current_message:
            current_message = current_message.replace("{emoji}", random.choice(EMOJIS))
        if "{random}" in current_message:
            current_message = current_message.replace("{random}", str(random.randint(1000, 9999)))
        if "{random_string}" in current_message:
            random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            current_message = current_message.replace("{random_string}", random_string)

        try:
            payload = {"content": current_message}
            response = session.post(
                f"https://discord.com/api/v9/channels/{channel}/messages",
                headers=self.headers(token),
                json=payload
            )
            logger.info(f"Spammer request for {token[:10]}...: Status {response.status_code}, Message: {current_message}")
            if response.status_code == 200:
                state.spammer_results.append({'token': token[:10] + '...', 'status': 'success', 'message': f"Message sent: {current_message}"})
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                logger.warning(f"Rate limited for {token[:10]}..., retrying after {retry_after}s")
                time.sleep(float(retry_after))
                self.spammer(token, channel, message, random_emojis, random_strings)
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
                self.token_checker(token)
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
        logger.info("No valid tokens found, running token checker first")
        state.checker_running = True
        state.checker_results = []

        def run_auto_checker():
            threads = []
            for token in state.tokens:
                thread = threading.Thread(target=raider.token_checker, args=(token,))
                threads.append(thread)
                thread.start()
                time.sleep(0.1)
            for thread in threads:
                thread.join()
            state.valid_tokens = [r['fullToken'] for r in state.checker_results if r['status'] == 'success']
            state.checker_running = False
            logger.info(f"Auto checker completed: {len(state.valid_tokens)} valid tokens")

            if not state.valid_tokens:
                logger.error("No valid tokens found after checking")
                state.joiner_results.append({'token': 'N/A', 'status': 'error', 'message': 'No valid tokens found'})
                return

            start_joiner(invite, delay, max_joins, max_threads)

        threading.Thread(target=run_auto_checker, daemon=True).start()
        return jsonify({'message': 'Checking tokens before joining', 'results': []})

    return start_joiner(invite, delay, max_joins, max_threads)

def start_joiner(invite, delay, max_joins, max_threads):
    invite_code = re.sub(r"(https?://)?(www\.)?(discord\.(gg|com)/(invite/)?|\.gg/)", "", invite)
    state.joiner_running = True
    state.joiner_results = []
    logger.info(f"Joiner started with invite: {invite_code}, tokens: {len(state.valid_tokens)}")

    if not state.proxies:
        logger.warning("No proxies provided - joining without proxies increases CAPTCHA risk")

    try:
        sample_token = state.valid_tokens[0]
        session = tls_client.Session(client_identifier="chrome_128", random_tls_extension_order=True)
        response = session.get(f"https://discord.com/api/v9/invites/{invite_code}", headers=raider.headers(sample_token))
        if response.status_code != 200:
            error_msg = response.json().get('message', f'HTTP {response.status_code}')
            logger.error(f"Invalid invite code {invite_code}: {error_msg}")
            state.joiner_results.append({'token': 'N/A', 'status': 'error', 'message': f"Invalid invite: {error_msg}"})
            state.joiner_running = False
            return jsonify({'message': f"Invalid invite: {error_msg}", 'results': state.joiner_results}), 400

        invite_info = response.json()
        guild_name = invite_info.get('guild', {}).get('name', 'Unknown')
        logger.info(f"Valid invite for server: {guild_name}")
    except Exception as e:
        logger.error(f"Error validating invite: {str(e)}")
        state.joiner_results.append({'token': 'N/A', 'status': 'error', 'message': f"Error validating invite: {str(e)}"})
        state.joiner_running = False
        return jsonify({'message': f"Error validating invite: {str(e)}", 'results': state.joiner_results}), 400

    def run_joiner():
        join_tokens = state.valid_tokens[:max_joins]
        active_threads = []
        used_proxies = set()

        for token in join_tokens:
            if not state.joiner_running:
                break

            available_proxies = [p for p in state.proxies if p not in used_proxies] if state.proxies else []
            proxy = random.choice(available_proxies) if available_proxies else None
            if proxy:
                used_proxies.add(proxy)

            while len(active_threads) >= max_threads:
                active_threads = [t for t in active_threads if t.is_alive()]
                time.sleep(0.1)

            thread = threading.Thread(target=raider.joiner, args=(token, invite_code, proxy))
            thread.daemon = True
            active_threads.append(thread)
            thread.start()

            time.sleep(random.uniform(delay, delay + 3))

        for thread in active_threads:
            if thread.is_alive():
                thread.join()

        state.joiner_running = False
        logger.info(f"Joiner completed: {len(state.joiner_results)} results")
        for result in state.joiner_results:
            if result['status'] == 'success':
                logger.info(f"{result['token']}: {result['message']}")
            else:
                logger.error(f"{result['token']}: {result['message']}")

    threading.Thread(target=run_joiner, daemon=True).start()
    return jsonify({'message': 'Joiner started', 'results': []})

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
        active_threads = []

        for token in leave_tokens:
            if not state.leaver_running:
                break

            while len(active_threads) >= max_threads:
                active_threads = [t for t in active_threads if t.is_alive()]
                time.sleep(0.1)

            thread = threading.Thread(target=raider.leaver, args=(token, guild_id))
            thread.daemon = True
            active_threads.append(thread)
            thread.start()

            time.sleep(delay)

        for thread in active_threads:
            if thread.is_alive():
                thread.join()

        state.leaver_running = False
        logger.info(f"Leaver completed: {len(state.leaver_results)} results")

    threading.Thread(target=run_leaver, daemon=True).start()
    return jsonify({'message': 'Leaver started', 'results': []})

@app.route('/spam', methods=['POST'])
def spam():
    data = request.json
    state.tokens = data.get('tokens', [])
    channel_id = data.get('channelId', '')
    message = data.get('message', '')
    delay = float(data.get('delay', 1))
    count = int(data.get('spamCount', 10))
    max_threads = int(data.get('maxThreads', 5))
    random_emojis = data.get('randomEmojis', False)
    random_strings = data.get('randomStrings', False)

    if not state.tokens or not channel_id or not message:
        logger.error("Spammer: Missing tokens, channel ID, or message")
        return jsonify({'message': 'Tokens, channel ID, or message required', 'results': []}), 400
    if not state.valid_tokens:
        logger.error("Spammer: No valid tokens found")
        return jsonify({'message': 'No valid tokens found. Run Checker first.', 'results': []}), 400

    state.spammer_running = True
    state.spammer_results = []
    logger.info(f"Spammer started with channel: {channel_id}, count: {count}, tokens: {len(state.valid_tokens)}, message: {message}, random_emojis: {random_emojis}, random_strings: {random_strings}")

    def run_spammer():
        spam_tokens = state.valid_tokens[:]
        for i in range(count):
            if not state.spammer_running:
                break

            active_threads = []
            for token in spam_tokens:
                thread = threading.Thread(target=raider.spammer, args=(token, channel_id, message, random_emojis, random_strings))
                thread.daemon = True
                active_threads.append(thread)
                thread.start()

                while len(active_threads) >= max_threads:
                    active_threads = [t for t in active_threads if t.is_alive()]
                    time.sleep(0.1)

                time.sleep(delay / len(spam_tokens))

            for thread in active_threads:
                if thread.is_alive():
                    thread.join()

            time.sleep(delay)

        state.spammer_running = False
        logger.info(f"Spammer completed: {len(state.spammer_results)} results")
        for result in state.spammer_results:
            if result['status'] == 'success':
                logger.info(f"{result['token']}: {result['message']}")
            else:
                logger.error(f"{result['token']}: {result['message']}")

    threading.Thread(target=run_spammer, daemon=True).start()
    return jsonify({'message': 'Spammer started', 'results': []})

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
        active_threads = []
        for token in state.tokens:
            if not state.checker_running:
                break

            while len(active_threads) >= max_threads:
                active_threads = [t for t in active_threads if t.is_alive()]
                time.sleep(0.1)

            thread = threading.Thread(target=raider.token_checker, args=(token,))
            thread.daemon = True
            active_threads.append(thread)
            thread.start()

            time.sleep(0.1)

        for thread in active_threads:
            if thread.is_alive():
                thread.join()

        state.valid_tokens = [r['fullToken'] for r in state.checker_results if r['status'] == 'success']
        state.checker_running = False
        logger.info(f"Checker completed: {len(state.valid_tokens)} valid tokens")

    threading.Thread(target=run_checker, daemon=True).start()
    return jsonify({'message': 'Checker started', 'results': []})

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
