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
import string
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', force=True)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')

class Proxy:
    def __init__(self, proxy_string, proxy_type="http"):
        self.proxy_string = proxy_string
        self.proxy_type = proxy_type.lower()
        self.ip = None
        self.port = None
        self.username = None
        self.password = None
        self.parse_proxy()

    def parse_proxy(self):
        patterns = [
            r'^(?P<ip>[^:]+):(?P<port>\d+)(?::(?P<user>[^:]+):(?P<pass>[^:]+))?$',
            r'^(?P<user>[^:]+):(?P<pass>[^@]+)@(?P<ip>[^:]+):(?P<port>\d+)$',
        ]
        for pattern in patterns:
            match = re.match(pattern, self.proxy_string)
            if match:
                self.ip = match.group('ip')
                self.port = match.group('port')
                self.username = match.group('user') if 'user' in match.groupdict() else None
                self.password = match.group('pass') if 'pass' in match.groupdict() else None
                return
        raise ValueError(f"Invalid proxy format: {self.proxy_string}")

    def to_dict(self):
        proxy_dict = {f"{self.proxy_type}": f"{self.ip}:{self.port}"}
        if self.username and self.password:
            proxy_dict = {f"{self.proxy_type}": f"{self.username}:{self.password}@{self.ip}:{self.port}"}
        return proxy_dict

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
        self.token_info = []
        self.fun_results = []

state = State()
EMOJIS = ['😀', '😂', '😍', '😎', '🤓', '👍', '👀', '🚀', '🔥', '💀']

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
]

class Raider:
    def __init__(self):
        self.cookies = "locale=en-US"

    def super_properties(self):
        payload = {
            "os": random.choice(["Windows", "Mac OS X", "Linux", "iOS"]),
            "browser": random.choice(["Chrome", "Firefox", "Safari", "Discord Client"]),
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

    def joiner(self, token, invite, proxy=None, max_retries=3):
        session = tls_client.Session(client_identifier=f"chrome_{random.randint(120, 128)}", random_tls_extension_order=True)
        session.timeout_seconds = 15

        if proxy:
            session.proxies = proxy.to_dict()
        elif state.proxies:
            proxy = random.choice(state.proxies)
            session.proxies = proxy.to_dict()

        retries = 0
        while retries < max_retries:
            try:
                invite_code = re.sub(r"(https?://)?(www\.)?(discord\.(gg|com)/(invite/)?|\.gg/)", "", invite)
                url = f"https://discord.com/api/v9/invites/{invite_code}"
                nonce = str(uuid.uuid4().int)
                payload = {"session_id": str(uuid.uuid4()), "nonce": nonce}

                logger.info(f"Joining with token: {token[:10]}..., invite: {invite_code}, proxy: {proxy.proxy_string if proxy else 'None'}")

                info_response = session.get(url, headers=self.headers(token))
                if info_response.status_code != 200:
                    error_msg = info_response.json().get('message', f'HTTP {info_response.status_code}')
                    state.joiner_results.append({'token': token[:10] + '...', 'status': 'error', 'message': f"Invalid invite: {error_msg}"})
                    return

                time.sleep(random.uniform(1, 3))

                response = session.post(url, headers=self.headers(token), json=payload)
                logger.info(f"Joiner response for {token[:10]}...: Status {response.status_code}")

                if response.status_code == 200:
                    guild_name = response.json().get('guild', {}).get('name', 'Unknown')
                    result = {'token': token[:10] + '...', 'status': 'success', 'message': f"Joined {guild_name}"}
                    state.joiner_results.append(result)
                    logger.info(f"{result['token']}: {result['message']}")
                    return
                elif response.status_code == 400 and 'captcha_key' in response.text:
                    logger.warning(f"Captcha required for {token[:10]}...")
                    retries += 1
                    if retries < max_retries and state.proxies:
                        new_proxy = random.choice([p for p in state.proxies if p != proxy])
                        logger.info(f"Retrying with new proxy: {new_proxy.proxy_string}")
                        proxy = new_proxy
                        session.proxies = proxy.to_dict()
                        time.sleep(random.uniform(5, 10))
                        continue
                    result = {'token': token[:10] + '...', 'status': 'error', 'message': "CAPTCHA required"}
                    state.joiner_results.append(result)
                    logger.error(f"{result['token']}: {result['message']}")
                    return
                elif response.status_code == 429:
                    retry_after = response.json().get('retry_after', 5)
                    logger.warning(f"Rate limited for {token[:10]}..., retrying after {retry_after}s")
                    time.sleep(float(retry_after))
                    retries += 1
                    continue
                else:
                    error_msg = response.json().get('message', f'HTTP {response.status_code}')
                    result = {'token': token[:10] + '...', 'status': 'error', 'message': error_msg}
                    state.joiner_results.append(result)
                    logger.error(f"{result['token']}: {result['message']}")
                    return
            except Exception as e:
                retries += 1
                if retries < max_retries:
                    time.sleep(random.uniform(2, 5))
                    continue
                result = {'token': token[:10] + '...', 'status': 'error', 'message': str(e)}
                state.joiner_results.append(result)
                logger.error(f"{result['token']}: {result['message']}")
                return

    def leaver(self, token, guild, proxy=None):
        session = tls_client.Session(client_identifier="chrome_128", random_tls_extension_order=True)
        session.timeout_seconds = 10
        if proxy:
            session.proxies = proxy.to_dict()
        elif state.proxies:
            proxy = random.choice(state.proxies)
            session.proxies = proxy.to_dict()

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
                self.leaver(token, guild, proxy)
            else:
                error_msg = response.json().get('message', f'HTTP {response.status_code}')
                state.leaver_results.append({'token': token[:10] + '...', 'status': 'error', 'message': error_msg})
        except Exception as e:
            state.leaver_results.append({'token': token[:10] + '...', 'status': 'error', 'message': str(e)})

    def spammer(self, token, channel, message, random_emojis=False, random_strings=False, add_everyone=False, proxy=None):
        session = tls_client.Session(client_identifier="chrome_128", random_tls_extension_order=True)
        session.timeout_seconds = 10
        if proxy:
            session.proxies = proxy.to_dict()
        elif state.proxies:
            proxy = random.choice(state.proxies)
            session.proxies = proxy.to_dict()

        current_message = message
        if random_emojis and "{emoji}" not in current_message:
            current_message += " {emoji}"
        if random_strings and "{random_string}" not in current_message:
            current_message += " {random_string}"
        if add_everyone:
            current_message += " @everyone"

        if "{emoji}" in current_message:
            current_message = current_message.replace("{emoji}", random.choice(EMOJIS))
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
            logger.info(f"Spammer request for {token[:10]}...: Status {response.status_code}")
            if response.status_code == 200:
                state.spammer_results.append({'token': token[:10] + '...', 'status': 'success', 'message': f"Message sent: {current_message}"})
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                logger.warning(f"Rate limited for {token[:10]}..., retrying after {retry_after}s")
                time.sleep(float(retry_after))
                self.spammer(token, channel, message, random_emojis, random_strings, add_everyone, proxy)
            else:
                error_msg = response.json().get('message', f'HTTP {response.status_code}')
                state.spammer_results.append({'token': token[:10] + '...', 'status': 'error', 'message': error_msg})
        except Exception as e:
            state.spammer_results.append({'token': token[:10] + '...', 'status': 'error', 'message': str(e)})

    def token_checker(self, token, proxy=None):
        session = tls_client.Session(client_identifier="chrome_128", random_tls_extension_order=True)
        session.timeout_seconds = 10
        if proxy:
            session.proxies = proxy.to_dict()
        elif state.proxies:
            proxy = random.choice(state.proxies)
            session.proxies = proxy.to_dict()

        try:
            response = session.get("https://discord.com/api/v9/users/@me/library", headers=self.headers(token))
            logger.info(f"Checker request for {token[:10]}...: Status {response.status_code}")
            if response.status_code == 200:
                user_data = session.get("https://discord.com/api/v9/users/@me", headers=self.headers(token)).json()
                verified = user_data.get('verified', False)
                nitro = bool(user_data.get('premium_type'))
                created_at = datetime.fromtimestamp(((int(user_data.get('id', 0)) >> 22) + 1420070400000) / 1000).strftime('%Y-%m-%d')
                token_info = {
                    'token': token[:10] + '...',
                    'fullToken': token,
                    'status': 'success',
                    'message': f"Valid{' (Nitro)' if nitro else ''}{' (Unverified)' if not verified else ''}",
                    'nitro': nitro,
                    'email': user_data.get('email', 'N/A'),
                    'created_at': created_at,
                    'username': user_data.get('username', 'N/A'),
                    'user_id': user_data.get('id', 'N/A'),
                    'avatar': f"https://cdn.discordapp.com/avatars/{user_data.get('id')}/{user_data.get('avatar')}.png" if user_data.get('avatar') else 'N/A',
                    'verified': verified
                }
                state.checker_results.append(token_info)
                state.token_info.append(token_info)
            elif response.status_code == 403:
                state.checker_results.append({'token': token[:10] + '...', 'fullToken': token, 'status': 'error', 'message': "Locked", 'nitro': False})
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                logger.warning(f"Rate limited for {token[:10]}..., retrying after {retry_after}s")
                time.sleep(float(retry_after))
                self.token_checker(token, proxy)
            else:
                error_msg = response.json().get('message', f'HTTP {response.status_code}')
                state.checker_results.append({'token': token[:10] + '...', 'fullToken': token, 'status': 'error', 'message': error_msg, 'nitro': False})
        except Exception as e:
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
        return jsonify({'message': 'Tokens or invite code required', 'results': []}), 400

    state.joiner_results = []  

    if not state.valid_tokens:
        state.checker_running = True
        state.checker_results = []
        state.token_info = []

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

    try:
        sample_token = state.valid_tokens[0]
        session = tls_client.Session(client_identifier="chrome_128", random_tls_extension_order=True)
        response = session.get(f"https://discord.com/api/v9/invites/{invite_code}", headers=raider.headers(sample_token))
        if response.status_code != 200:
            error_msg = response.json().get('message', f'HTTP {response.status_code}')
            state.joiner_results.append({'token': 'N/A', 'status': 'error', 'message': f"Invalid invite: {error_msg}"})
            state.joiner_running = False
            return jsonify({'message': f"Invalid invite: {error_msg}", 'results': state.joiner_results}), 400

        logger.info(f"Valid invite for server: {response.json().get('guild', {}).get('name', 'Unknown')}")
    except Exception as e:
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

            available_proxies = [p for p in state.proxies if p.proxy_string not in used_proxies] if state.proxies else []
            proxy = random.choice(available_proxies) if available_proxies else None
            if proxy:
                used_proxies.add(proxy.proxy_string)

            while len(active_threads) >= max_threads:
                active_threads = [t for t in active_threads if t.is_alive()]
                time.sleep(0.1)

            thread = threading.Thread(target=raider.joiner, args=(token, invite_code, proxy))
            thread.daemon = True
            active_threads.append(thread)
            thread.start()

            time.sleep(random.uniform(delay, delay + 3))

        for thread in active_threads:
            thread.join()

        state.joiner_running = False
        logger.info(f"Joiner completed: {len(state.joiner_results)} results")

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
        return jsonify({'message': 'Tokens or guild ID required', 'results': []}), 400
    if not state.valid_tokens:
        return jsonify({'message': 'No valid tokens found. Run Checker first.', 'results': []}), 400

    state.leaver_results = []
    state.leaver_running = True

    def run_leaver():
        leave_tokens = state.valid_tokens[:]
        active_threads = []

        for token in leave_tokens:
            if not state.leaver_running:
                break

            while len(active_threads) >= max_threads:
                active_threads = [t for t in active_threads if t.is_alive()]
                time.sleep(0.1)

            proxy = random.choice(state.proxies) if state.proxies else None
            thread = threading.Thread(target=raider.leaver, args=(token, guild_id, proxy))
            thread.daemon = True
            active_threads.append(thread)
            thread.start()

            time.sleep(delay)

        for thread in active_threads:
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
    disable_delay = data.get('disableDelay', False)
    count = int(data.get('spamCount', 10))
    max_threads = int(data.get('maxThreads', 5))
    random_emojis = data.get('randomEmojis', False)
    random_strings = data.get('randomStrings', False)
    add_everyone = data.get('addEveryone', False)

    if not state.tokens or not channel_id or not message:
        return jsonify({'message': 'Tokens, channel ID, or message required', 'results': []}), 400
    if not state.valid_tokens:
        return jsonify({'message': 'No valid tokens found. Run Checker first.', 'results': []}), 400

    state.spammer_results = []
    state.spammer_running = True

    def run_spammer():
        spam_tokens = state.valid_tokens[:]
        for i in range(count):
            if not state.spammer_running:
                break

            active_threads = []
            for token in spam_tokens:
                proxy = random.choice(state.proxies) if state.proxies else None
                thread = threading.Thread(target=raider.spammer, args=(token, channel_id, message, random_emojis, random_strings, add_everyone, proxy))
                thread.daemon = True
                active_threads.append(thread)
                thread.start()

                while len(active_threads) >= max_threads:
                    active_threads = [t for t in active_threads if t.is_alive()]
                    time.sleep(0.1)

                if not disable_delay:
                    time.sleep(delay / len(spam_tokens))

            for thread in active_threads:
                thread.join()

            if not disable_delay:
                time.sleep(delay)

        state.spammer_running = False
        logger.info(f"Spammer completed: {len(state.spammer_results)} results")

    threading.Thread(target=run_spammer, daemon=True).start()
    return jsonify({'message': 'Spammer started', 'results': []})

@app.route('/check', methods=['POST'])
def check():
    data = request.json
    state.tokens = data.get('tokens', [])
    max_threads = int(data.get('maxThreads', 5))

    if not state.tokens:
        return jsonify({'message': 'Tokens required', 'results': []}), 400

    state.checker_results = []
    state.valid_tokens = []
    state.token_info = []
    state.checker_running = True

    def run_checker():
        active_threads = []
        for token in state.tokens:
            if not state.checker_running:
                break

            while len(active_threads) >= max_threads:
                active_threads = [t for t in active_threads if t.is_alive()]
                time.sleep(0.1)

            proxy = random.choice(state.proxies) if state.proxies else None
            thread = threading.Thread(target=raider.token_checker, args=(token, proxy))
            thread.daemon = True
            active_threads.append(thread)
            thread.start()

            time.sleep(0.1)

        for thread in active_threads:
            thread.join()

        state.valid_tokens = [r['fullToken'] for r in state.checker_results if r['status'] == 'success']
        state.checker_running = False
        logger.info(f"Checker completed: {len(state.valid_tokens)} valid tokens")

    threading.Thread(target=run_checker, daemon=True).start()
    return jsonify({'message': 'Checker started', 'results': []})

@app.route('/fun_ghost_pinger', methods=['POST'])
def fun_ghost_pinger():
    data = request.json
    state.tokens = data.get('tokens', [])
    channel_id = data.get('channelId', '')
    mention = data.get('mention', '')
    max_threads = int(data.get('maxThreads', 5))

    if not state.tokens or not channel_id or not mention:
        return jsonify({'message': 'Tokens, channel ID, or mention required', 'results': []}), 400
    if not state.valid_tokens:
        return jsonify({'message': 'No valid tokens found. Run Checker first.', 'results': []}), 400

    state.fun_results = []

    def run_ghost_pinger():
        active_threads = []
        for token in state.valid_tokens:
            while len(active_threads) >= max_threads:
                active_threads = [t for t in active_threads if t.is_alive()]
                time.sleep(0.1)

            proxy = random.choice(state.proxies) if state.proxies else None
            thread = threading.Thread(target=raider.ghost_pinger, args=(token, channel_id, mention, proxy))
            thread.daemon = True
            active_threads.append(thread)
            thread.start()

            time.sleep(0.1)

        for thread in active_threads:
            thread.join()

        logger.info(f"Ghost Pinger completed: {len(state.fun_results)} results")

    threading.Thread(target=run_ghost_pinger, daemon=True).start()
    return jsonify({'message': 'Ghost Pinger started', 'results': []})

@app.route('/fun_button_spammer', methods=['POST'])
def fun_button_spammer():
    data = request.json
    state.tokens = data.get('tokens', [])
    message_link = data.get('messageLink', '')
    click_count = int(data.get('clickCount', 5))
    fetch_channel = data.get('fetchChannel', False)
    max_threads = int(data.get('maxThreads', 5))

    if not state.tokens or not message_link:
        return jsonify({'message': 'Tokens or message link required', 'results': []}), 400
    if not state.valid_tokens:
        return jsonify({'message': 'No valid tokens found. Run Checker first.', 'results': []}), 400

    state.fun_results = []

    def run_button_spammer():
        active_threads = []
        for token in state.valid_tokens:
            while len(active_threads) >= max_threads:
                active_threads = [t for t in active_threads if t.is_alive()]
                time.sleep(0.1)

            proxy = random.choice(state.proxies) if state.proxies else None
            thread = threading.Thread(target=raider.button_spammer, args=(token, message_link, click_count, fetch_channel, proxy))
            thread.daemon = True
            active_threads.append(thread)
            thread.start()

            time.sleep(0.1)

        for thread in active_threads:
            thread.join()

        logger.info(f"Button Spammer completed: {len(state.fun_results)} results")

    threading.Thread(target=run_button_spammer, daemon=True).start()
    return jsonify({'message': 'Button Spammer started', 'results': []})

@app.route('/fun_emoji_reaction', methods=['POST'])
def fun_emoji_reaction():
    data = request.json
    state.tokens = data.get('tokens', [])
    channel_id = data.get('channelId', '')
    message_id = data.get('messageId', '')
    emojis = data.get('emojis', [])
    max_threads = int(data.get('maxThreads', 5))

    if not state.tokens or not channel_id or not message_id or not emojis:
        return jsonify({'message': 'Tokens, channel ID, message ID, or emojis required', 'results': []}), 400
    if not state.valid_tokens:
        return jsonify({'message': 'No valid tokens found. Run Checker first.', 'results': []}), 400

    state.fun_results = []

    def run_emoji_reaction():
        active_threads = []
        for token in state.valid_tokens:
            while len(active_threads) >= max_threads:
                active_threads = [t for t in active_threads if t.is_alive()]
                time.sleep(0.1)

            proxy = random.choice(state.proxies) if state.proxies else None
            thread = threading.Thread(target=raider.emoji_reaction, args=(token, channel_id, message_id, emojis, proxy))
            thread.daemon = True
            active_threads.append(thread)
            thread.start()

            time.sleep(0.1)

        for thread in active_threads:
            thread.join()

        logger.info(f"Emoji Reaction completed: {len(state.fun_results)} results")

    threading.Thread(target=run_emoji_reaction, daemon=True).start()
    return jsonify({'message': 'Emoji Reaction started', 'results': []})

@app.route('/fun_guild_info', methods=['POST'])

@app.route('/stop_joiner', methods=['POST'])
def stop_joiner():
    state.joiner_running = False
    return jsonify({'message': 'Joiner stopped'})

@app.route('/stop_leaver', methods=['POST'])
def stop_leaver():
    state.leaver_running = False
    return jsonify({'message': 'Leaver stopped'})

@app.route('/stop_spammer', methods=['POST'])
def stop_spammer():
    state.spammer_running = False
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
        'valid_tokens': len(state.valid_tokens),
        'token_info': state.token_info,
        'fun_results': state.fun_results
    })

@app.route('/proxies', methods=['POST'])
def save_proxies():
    data = request.json
    proxies_data = data.get('proxies', [])
    state.proxies = []
    for proxy in proxies_data:
        try:
            proxy_string = proxy.get('proxy_string', '')
            proxy_type = proxy.get('proxy_type', 'http')
            if proxy_type not in ['http', 'https', 'socks4', 'socks5']:
                proxy_type = 'http'
            state.proxies.append(Proxy(proxy_string, proxy_type))
        except ValueError as e:
            logger.error(f"Failed to parse proxy {proxy_string}: {str(e)}")
    logger.info(f"Saved {len(state.proxies)} proxies")
    return jsonify({'message': f"Saved {len(state.proxies)} proxies"})

@app.route('/export_tokens', methods=['GET'])
def export_tokens():
    return jsonify({'tokens': state.token_info})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
