import os
import re
import select
import socket
import ssl
import struct
import threading
import time
from enum import IntEnum
from urllib.parse import unquote

import certifi

from pyload.core.network.exceptions import Abort
from pyload.core.utils import format
from pyload.core.utils.convert import to_bytes, to_str
from pyload.core.utils.struct.lock import lock
from pyload.core.utils.web.check import get_public_address, is_global_address
from pyload.core.utils.web.convert import host_to_ip

from ..base.addon import threaded
from ..base.downloader import BaseDownloader


class IRC:
    class SSLUsage(IntEnum):
        FALSE = 0
        TRUE = 1
        STARTTLS = 2

    def __init__(self, plugin, nick, ident, realname):
        self.plugin = plugin
        self._ = plugin._
        self.lock = threading.RLock()

        #: last 4 digits
        self.nick = (
            "pyload-{:04.0f}".format(time.time() % 10000) if nick == "pyload" else nick
        )
        self.ident = ident
        self.realname = realname

        self.irc_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tls_active = False
        self.sent_caps = False

        self.receive_buffer = ""
        self.lines = []

        self.connected = False
        self.host = ""
        self.port = 0

        self.motd_lines = []
        self.server_capabilities = {}

        self.xdcc_bot_hosts = {}
        self.xdcc_request_time = 0
        self.xdcc_queue_query_time = 0

    def _data_available(self):
        fdset = select.select([self.irc_sock], [], [], 0)
        return self.irc_sock in fdset[0]

    def _send_line(self, line):
        """
        Send a single IRC line terminated by CRLF.
        Guards against CRLF injection by stripping internal newlines.
        """
        if not self.irc_sock:
            return

        clean_line = line.rstrip("\r\n")
        if "\r" in clean_line or "\n" in clean_line:
            self.plugin.log_warning(self._("CRLF injection attempt detected in IRC command"))
            clean_line = clean_line.replace("\r", "").replace("\n", "")

        self.irc_sock.send(to_bytes(clean_line + "\r\n"))

    def _get_response_line(self, timeout=5):
        start_time = time.monotonic()
        while time.monotonic() - start_time < timeout:
            if self._data_available():
                receive_bytes = self.irc_sock.recv(1 << 10)
                try:
                    self.receive_buffer += to_str(receive_bytes)
                except UnicodeDecodeError:
                    self.receive_buffer += to_str(receive_bytes, encoding="iso-8859-1")

                self.lines += self.receive_buffer.split("\r\n")
                self.receive_buffer = self.lines.pop()

            if self.lines:
                return self.lines.pop(0)

            else:
                time.sleep(0.1)

        return None

    def _parse_irc_msg(self, line):
        """
        Breaks a message from an IRC server into its origin, command, and arguments.
        """
        origin = ""
        if not line:
            return None, None, None

        if line[0] == ":":
            origin, line = line[1:].split(" ", 1)

        if line.find(" :") != -1:
            line, trailing = line.split(" :", 1)
            args = line.split()
            args.append(trailing)

        else:
            args = line.split()

        command = args.pop(0)

        return origin, command, args

    @lock
    def _handle_motd(self):
        motd_start = False
        start_time = time.monotonic()
        while time.monotonic() - start_time < 30:
            origin, command, args = self.get_irc_command()
            if command == '375':  #: RPL_MOTDSTART
                motd_start = True

            elif motd_start and command == '372':  #: RPL_MOTD
                motd_text = args[1]
                self.motd_lines.append(motd_text)

            elif motd_start and command in ('376', '422'):  #: RPL_ENDOFMOTD, ERR_NOMOTD
                break

    @lock
    def connect_server(self, host, port, use_ssl=SSLUsage.FALSE):
        """
        Connect to the IRC server and wait for RPL_WELCOME message.
        """
        if self.connected:
            self.plugin.log_warning(
                self._("Already connected to server, not connecting")
            )
            return False

        host_ips = host_to_ip(host)
        if not any(is_global_address(ip) for ip in host_ips):
            self.plugin.log_error(self._("IRC Server {} resolves to private or reserved IP addresses received").format(host))
            return False

        self.plugin.log_info(self._("Connecting to: {}:{}").format(host, port))
        self.host = host
        self.port = port

        self.irc_sock.settimeout(90)
        self.irc_sock.connect((host_ips[0], port))
        self.irc_sock.settimeout(None)

        #: flush input
        for _ in range(5):
            if not self._get_response_line():
                break

        starttls_acknowledged = False
        if use_ssl == IRC.SSLUsage.STARTTLS:
            if self.get_server_capabilities("tls", force_query=True, end_caps=False):
                self.plugin.log_debug(self._("TLS via STARTTLS supported, attempting connection upgrade"))
                self._send_line("STARTTLS")
                start_time = time.monotonic()
                while time.monotonic() - start_time < 30:
                    origin, command, args = self.get_irc_command()
                    if command == '670':  #: RPL_STARTTLS
                        starttls_acknowledged = True
                        break
                    elif command == "691":
                        self.plugin.log_warning(self._("STARTTLS handshake failed with {} {}").format(command, args[1]))
                        break

                if not starttls_acknowledged:
                    self.irc_sock.close()
                    return False

            else:
                self.plugin.log_error(self._("TLS via STARTTLS unsupported, disconnecting"))
                self.irc_sock.close()
                return False

        if use_ssl == IRC.SSLUsage.TRUE or starttls_acknowledged:
            try:
                self.plugin.log_debug(self._("Attempting TLS handshake.."))
                context = ssl.create_default_context(cafile=certifi.where())
                context.verify_mode = ssl.CERT_REQUIRED
                context.check_hostname = True
                context.minimum_version = ssl.TLSVersion.TLSv1_2  # Strong TLS
                self.irc_sock = context.wrap_socket(
                    self.irc_sock,
                    server_hostname=self.host,
                    do_handshake_on_connect=True
                )
                self.tls_active = True
                self.plugin.log_debug(self._("TLS handshake successful - Cipher:{}, Version:{}, Bits:{}").format(
                    *self.irc_sock.cipher()
                ))

            except ssl.SSLCertVerificationError as exc:
                self.plugin.log_error(self._("certificate verification failed {}").format(exc))
                self.irc_sock.close()
                return False
            except ssl.SSLError as exc:
                self.plugin.log_error(self._("TLS handshake failed {}").format(exc))
                self.irc_sock.close()
                return False

        self.end_capabilities_mode()

        #: flush input
        for _ in range(5):
            if not self._get_response_line():
                break

        self._send_line("NICK {}".format(self.nick))
        self._send_line("USER {} {} bla :{}".format(self.ident, host, self.realname))

        start_time = time.monotonic()
        while time.monotonic() - start_time < 30:
            origin, command, args = self.get_irc_command()
            if command == "001":  #: RPL_WELCOME
                self.connected = True

                #: Skip MOTD
                self._handle_motd()

                #: Read a few more lines after MOTD
                for _ in range(5):
                    if not self._get_response_line():
                        break

                self.plugin.log_debug(
                    self._("Successfully connected to {}:{}").format(host, port)
                )

                return True

            elif command == "432":  #: ERR_ERRONEUSNICKNAME
                self.plugin.log_error(self._("Illegal nickname: {}").format(self.nick))
                break

            elif command == "433":  #: ERR_NICKNAMEINUSE
                self.plugin.log_error(
                    self._("Nickname {} is already in use").format(self.nick)
                )
                break

        self.plugin.log_error(self._("Connection to {}:{} failed").format(host, port))
        return False

    @lock
    def disconnect_server(self):
        if self.connected:
            self.plugin.log_info(
                self._("Disconnecting from {}:{}").format(self.host, self.port)
            )
            self._send_line("QUIT :byebye")
            self.plugin.log_debug("Disconnected")
            self.connected = False

        else:
            self.plugin.log_warning(
                self._("Not connected to server, cannot disconnect")
            )

        self.irc_sock.close()

    @lock
    def get_server_capabilities(self, capability=None, force_query=False, end_caps=True):
        def _parse_cap_value(value):
            if '=' in value:
                return {k.strip(): v.strip() for k, v in re.findall(r'([^,=]+)=([^,=]+)', value)}
            elif ',' in value:
                return [item.strip() for item in value.split(',')]
            elif value == "":
                return True
            else:
                return value

        try:
            if capability is None:
                self.plugin.log_info(self._("Querying server capabilities").format(capability))
            else:
                self.plugin.log_info(self._("Querying server for {} capability").format(capability))

            if force_query or not self.server_capabilities:
                self._send_line("CAP LS")
                self._send_line("PING :{}".format(self.host))
                self.sent_caps = True
                start_time = time.monotonic()
                while time.monotonic() - start_time < 30:
                    origin, command, args = self.get_irc_command()
                    if command == 'CAP' and args[1] == 'LS':
                        self.server_capabilities = dict(
                            (t[0], _parse_cap_value(t[1]))
                            for t in re.findall(r'([a-zA-Z0-9_./-]+)(?:=([^ ]*))?', args[2])
                        )
                        break

            if capability is None:
                self.plugin.log_debug(self._("Server capabilities: {}").format(self.server_capabilities))
                return self.server_capabilities
            else:
                cap = self.server_capabilities.get(capability)
                self.plugin.log_debug(self._("Server capability {}: {}").format(
                    capability, "N/A" if cap is None else cap
                ))
                return cap
        finally:
            if end_caps:
                self.end_capabilities_mode()

    def end_capabilities_mode(self):
        if self.sent_caps:
            self._send_line("CAP END")
            self.sent_caps = False

    @lock
    def get_irc_command(self):
        origin, command, args = None, None, None
        while True:
            line = self._get_response_line()
            origin, command, args = self._parse_irc_msg(line)

            if command == "PING":
                self.plugin.log_debug(f"[{args[0]}] Ping? Pong!")
                self._send_line("PONG :{}".format(args[0]))

            elif origin and command == "PRIVMSG":
                sender_nick = origin.split("@")[0].split("!")[0]
                recipient = args[0]
                text = args[1]

                if text[0] == "\x01" and text[-1] == "\x01":  #: CTCP
                    ctcp_data = text[1:-1].split(" ", 1)
                    ctcp_command = ctcp_data[0]
                    ctcp_args = ctcp_data[1] if len(ctcp_data) > 1 else ""

                    if recipient[0 : len(self.nick)] == self.nick:
                        if ctcp_command == "VERSION":
                            self.plugin.log_debug(
                                self._("[{}] CTCP VERSION").format(sender_nick)
                            )
                            self._send_line("NOTICE {} :\x01VERSION {}\x01".format(sender_nick, "pyLoad! IRC Interface"))

                        elif ctcp_command == "TIME":
                            self.plugin.log_debug(
                                self._("[{}] CTCP TIME").format(sender_nick)
                            )
                            self._send_line(
                                "NOTICE {} :\x01{}\x01".format(
                                    sender_nick,
                                    time.strftime("%a %b %d %H:%M:%S %Y"),
                                )
                            )

                        elif ctcp_command == "PING":
                            self.plugin.log_debug(
                                self._("[{}] Ping? Pong!").format(sender_nick)
                            )
                            self._send_line("NOTICE {} :\x01PING {}\x01".format(sender_nick, ctcp_args))  # NOTE: PING is not a typo

                        else:
                            break

                else:
                    break

            else:
                break

        return origin, command, args

    @lock
    def join_channel(self, chan):
        chan = "#" + chan if chan[0] != "#" else chan

        self.plugin.log_info(self._("Joining channel {}").format(chan))
        self._send_line("JOIN {}".format(chan))

        start_time = time.monotonic()
        while time.monotonic() - start_time < 30:
            origin, command, args = self.get_irc_command()

            #: ERR_KEYSET, ERR_CHANNELISFULL, ERR_INVITEONLYCHAN, ERR_BANNEDFROMCHAN, ERR_BADCHANNELKEY
            if (
                command in ("467", "471", "473", "474", "475")
                and args[1].lower() == chan.lower()
            ):
                self.plugin.log_error(
                    self._("Cannot join channel {} (error {}: '{}')").format(
                        chan, command, args[2]
                    )
                )
                return False

            elif command == "353" and args[2].lower() == chan.lower():  #: RPL_NAMREPLY
                self.plugin.log_debug(f"Successfully joined channel {chan}")
                return True

        return False

    @lock
    def send_private_message(self, bot, message, ctcp=False):
        clean_bot = bot.replace("\r", " ").replace("\n", " ").split()[0]
        clean_msg = message.replace("\r", "").replace("\n", "")
        if ctcp:
            self._send_line("PRIVMSG {} :\x01{}\x01".format(clean_bot, clean_msg))
        else:
            self._send_line("PRIVMSG {} :{}".format(clean_bot, clean_msg))
    @lock
    def nickserv_identify(self, password):
        self.plugin.log_info(self._("Authenticating nickname"))

        bot = "nickserv"
        bot_host = self.get_bot_host(bot)

        if not bot_host:
            self.plugin.log_warning(
                self._("Server does not seems to support nickserv commands")
            )
            return

        self.send_private_message(bot, "identify {}".format(password))

        start_time = time.monotonic()
        while time.monotonic() - start_time < 30:
            origin, command, args = self.get_irc_command()

            if origin is None or command is None or args is None:
                return

            # Private message from bot to us?
            if not self.is_message_from_target(origin, command, args, bot, bot_host):
                continue

            text = args[1]
            sender_nick = origin.split("@")[0].split("!")[0]
            self.plugin.log_info(self._("PrivMsg: <{}> {}").format(sender_nick, text))
            break

        else:
            self.plugin.log_warning(
                self._("'{}' did not respond to the request").format(bot)
            )

    @lock
    def send_invite_request(self, bot, chan, password):
        bot_host = self.get_bot_host(bot)
        if bot_host:
            self.plugin.log_info(
                self._("Sending invite request for #{} to '{}'").format(chan, bot)
            )
        else:
            self.plugin.log_warning(self._("Cannot send invite request"))
            return

        self.send_private_message(bot, "enter #{} {} {}".format(chan, self.nick, password))

        start_time = time.monotonic()
        while time.monotonic() - start_time < 30:
            origin, command, args = self.get_irc_command()

            if origin is None or command is None or args is None:
                return

            # Private message from bot to us?
            if not self.is_message_from_target(
                origin, command, args, bot, bot_host, allowed_commands=("PRIVMSG", "NOTICE", "INVITE")
            ):
                continue

            text = args[1]
            sender_nick = origin.split("@")[0].split("!")[0]
            if command == "INVITE":
                self.plugin.log_info(self._("Got invite to #{}").format(chan))

            else:
                self.plugin.log_info(
                    self._("PrivMsg: <{}> {}").format(sender_nick, text)
                )

            break

        else:
            self.plugin.log_warning(
                self._("'{}' did not respond to the request").format(bot)
            )

    @lock
    def is_bot_online(self, bot):
        self.plugin.log_info(self._("Checking if bot '{}' is online").format(bot))
        self._send_line("WHOIS {}".format(bot))

        start_time = time.monotonic()
        while time.monotonic() - start_time < 30:
            origin, command, args = self.get_irc_command()
            if (
                command == "401"
                and args[0] == self.nick
                and args[1].lower() == bot.lower()
            ):  #: ERR_NOSUCHNICK
                self.plugin.log_debug(f"Bot '{bot}' is offline")
                return False

            #: RPL_WHOISUSER
            elif (
                command == "311"
                and args[0] == self.nick
                and args[1].lower() == bot.lower()
            ):
                self.plugin.log_debug(f"Bot '{bot}' is online")
                self.xdcc_bot_hosts[bot] = args[3]  #: bot host
                return True

            else:
                time.sleep(0.1)

        else:
            self.plugin.log_error(self._("Server did not respond in a reasonable time"))
            return False

    @lock
    def get_bot_host(self, bot):
        bot_host = self.xdcc_bot_hosts.get(bot)
        if bot_host:
            return bot_host

        else:
            if self.is_bot_online(bot):
                return self.xdcc_bot_hosts.get(bot)

            else:
                return None

    def is_message_from_target(
        self, origin, command, args, target_bot, target_host=None, allowed_commands=("PRIVMSG", "NOTICE")
    ):
        """
        Validates that an incoming IRC message originated from the expected bot/service
        and was privately addressed to our client nickname.
        """
        if not origin or not command or not args or len(args) < 2:
            return False

        if command not in allowed_commands:
            return False

        if args[0].lower() != self.nick.lower():
            return False

        sender_nick = origin.split("!", 1)[0] if "!" in origin else origin.split("@", 1)[0]
        sender_host = origin.split("@", 1)[1] if "@" in origin else None

        if sender_nick.lower() != target_bot.lower():
            return False

        if target_host and (not sender_host or sender_host.lower() != target_host.lower()):
            self.plugin.log_warning(
                self._("Rejected message from '{}' due to host mismatch ('{}' != '{}')").format(
                    sender_nick, sender_host or "unknown", target_host
                )
            )
            return False

        return True

    @lock
    def xdcc_request_pack(self, bot, pack):
        self.plugin.log_info(self._("Requesting pack #{}").format(pack))
        self.xdcc_request_time = time.monotonic()
        self.send_private_message(bot, "xdcc send #{}".format(pack))

    @lock
    def xdcc_cancel_pack(self, bot):
        if self.xdcc_request_time:
            self.plugin.log_info(self._("Requesting XDCC cancellation"))
            self.xdcc_request_time = 0
            self.send_private_message(bot, "xdcc cancel")

        else:
            self.plugin.log_warning(self._("No XDCC request pending, cannot cancel"))

    @lock
    def xdcc_remove_queued(self, bot):
        if self.xdcc_request_time:
            self.plugin.log_info(self._("Requesting XDCC remove from queue"))
            self.xdcc_request_time = 0
            self.send_private_message(bot, "xdcc remove")

        else:
            self.plugin.log_warning(
                self._("No XDCC request pending, cannot remove from queue")
            )

    @lock
    def xdcc_query_queue_status(self, bot):
        if self.xdcc_request_time:
            self.plugin.log_info(self._("Requesting XDCC queue status"))
            self.xdcc_queue_query_time = time.monotonic()
            self.send_private_message(bot, "xdcc queue")

        else:
            self.plugin.log_warning(
                self._("No XDCC request pending, cannot query queue status")
            )

    @lock
    def xdcc_request_resume(self, bot, dcc_port, file_name, resume_position, dcc_token=None):
        if self.xdcc_request_time:
            bot_host = self.get_bot_host(bot)

            self.plugin.log_info(
                self._("Requesting XDCC resume of '{}' at position {}").format(
                    file_name, resume_position
                )
            )

            self.send_private_message(
                bot,
                'DCC RESUME "{}" {} {}{}'.format(
                    os.fsdecode(file_name),
                    dcc_port,
                    resume_position,
                    "" if dcc_token is None else f" {dcc_token}"
                ),
                ctcp=True
            )

            start_time = time.monotonic()
            while time.monotonic() - start_time < 30:
                origin, command, args = self.get_irc_command()

                # Private message from bot to us?
                if self.is_message_from_target(origin, command, args, bot, bot_host):

                    text = args[1]
                    sender_nick = origin.split("@")[0].split("!")[0]
                    self.plugin.log_debug(
                        self._("PrivMsg: <{}> {}").format(sender_nick, text)
                    )

                    m = re.match(
                        r"\x01DCC ACCEPT .*? {} (?P<RESUME_POS>\d+)(?: (?P<TOKEN>\d+))?\x01".format(
                            dcc_port
                        ),
                        text,
                    )
                    if m:
                        self.plugin.log_debug(
                            self._(
                                "Bot '{}' acknowledged resume at position {}"
                            ).format(sender_nick, m.group("RESUME_POS"))
                        )
                        return int(m.group("RESUME_POS"))

                else:
                    time.sleep(0.1)

            self.plugin.log_warning(
                self._("Timeout while waiting for resume acknowledge, not resuming")
            )

        else:
            self.plugin.log_error(self._("No XDCC request pending, cannot resume"))

        return 0

    @lock
    def xdcc_get_pack_info(self, bot, pack):
        bot_host = self.get_bot_host(bot)

        self.plugin.log_info(self._("Requesting pack #{} info").format(pack))
        self.send_private_message(bot, "xdcc info #{}".format(pack))

        info = {}
        start_time = time.monotonic()
        while time.monotonic() - start_time < 90:
            origin, command, args = self.get_irc_command()

            # Private message from bot to us?
            if self.is_message_from_target(origin, command, args, bot, bot_host):

                text = args[1]
                pack_info = text.split()
                if pack_info[0].lower() == "filename":
                    self.plugin.log_debug(f"Filename: '{pack_info[1]}'")
                    info.update({"status": "online", "name": pack_info[1]})

                elif pack_info[0].lower() == "filesize":
                    self.plugin.log_debug(f"Filesize: '{pack_info[1]}'")
                    info.update({"status": "online", "size": pack_info[1]})

                else:
                    sender_nick = origin.split("@")[0].split("!")[0]
                    self.plugin.log_debug(
                        self._("PrivMsg: <{}> {}").format(sender_nick, text)
                    )

            else:
                if len(info) > 2:  #: got both name and size
                    break

                time.sleep(0.1)

        else:
            if len(info) == 0:
                self.plugin.log_error(
                    self._("XDCC Bot '{}' did not answer").format(bot)
                )
                return {"status": "offline", "msg": "XDCC Bot did not answer"}

        return info


class XDCC(BaseDownloader):
    __name__ = "XDCC"
    __type__ = "downloader"
    __version__ = "0.58"
    __status__ = "testing"

    __pattern__ = r"(?P<PROTO>xdccs?)://(?P<SERVER>.*?)/#?(?P<CHAN>.*?)/(?P<BOT>.*?)/#?(?P<PACK>\d+)/?"
    __config__ = [
        ("nick", "str", "Nickname", "pyload"),
        ("ident", "str", "Ident", "pyloadident"),
        ("realname", "str", "Realname", "pyloadreal"),
        ("try_resume", "bool", "Request XDCC resume?", True),
        ("nick_pw", "str", "Registered nickname password (optional)", ""),
        ("queued_timeout", "int","Time to wait before failing if queued (minutes, 0 = infinite)", 300),
        ("queue_query_interval", "int", "Interval to query queue position when queued (minutes, 0 = disabled)", 3),
        ("response_timeout", "int", "XDCC Bot response timeout (seconds, minimum 60)", 300),
        ("passive_port", "int", "Passive XDCC port (0 to disable passive XDCC)", 0),
        ("waiting_opts",
            "str",
            "Time to wait before requesting pack from the XDCC Bot (format: ircserver/channel/wait_seconds, ...)",
            "",
        ),
        ("invite_opts", "str", "Invite bots options (format ircserver/channel/invitebot/password, ...)", ""),
        (
            "channel_opts",
            "str",
            "Join custom channel before joining channel (format: ircserver/channel/customchannel, ...)",
            "",
        ),
        (
            "tls_opts",
            "str",
            "TLS options (format: ircserver/*/true, ircserver/channel/true, ircserver/channel/starttls, ...)",
            "",
        ),
        ("default_tls_mode", "off;on;starttls", "Default TLS mode", "off"),
    ]

    __description__ = """Download from IRC XDCC bot"""
    __license__ = "GPLv3"
    __authors__ = [
        ("jeix", "jeix@hasnomail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    RE_QUEUED = re.compile(
        r'Added you to the (?:main|idle) queue for pack \d+ \("[^"]+"\) in position (\d+)'
    )
    RE_QUEUE_STAT = re.compile(
        r'^Queued \w+ for ".+?", in position (\d+).+?([\dhm]+) or less remaining'
    )
    RE_XDCC = re.compile(
        r'\x01DCC SEND "?(?P<NAME>.*?)"? (?P<IP>\d+) (?P<PORT>\d+)(?: (?P<SIZE>\d+))?(?: (?P<TOKEN>\d+))?\x01'
    )
    RE_XDCC_SSEND = re.compile(
        r'\x01DCC SSEND "?(?P<NAME>.*?)"? (?P<IP>\d+) (?P<PORT>\d+)(?: (?P<SIZE>\d+))?(?: (?P<TOKEN>\d+))?\x01'
    )

    def setup(self):
        self.dl_started = False
        self.dl_finished = False
        self.last_response_time = 0
        self.queued_time = 0

        self.irc_client = None
        self.last_exception = None

        self.dcc_port = 0
        self.dcc_file_name = ""
        self.dcc_sender_bot = None

        self.multi_dl = False

    def xdcc_send_resume(self, resume_position, dcc_token=None):
        if not self.config.get("try_resume") or not self.dcc_sender_bot:
            return 0

        return self.irc_client.xdcc_request_resume(
            self.dcc_sender_bot, self.dcc_port, self.dcc_file_name, resume_position, dcc_token
        )

    def xdcc_initiate_passive(self, xdcc_token):
        # Send CTCP DCC SEND reply with our ip/port
        external_ip = get_public_address()
        if not external_ip:
            self.log_error(self._("Could not determine external IP address for passive XDCC"))
            return
        ip_int = struct.unpack("!I", socket.inet_aton(external_ip))[0]

        self.irc_client.send_private_message(
            self.dcc_sender_bot,
            'DCC SEND "{}" {} {} {} {}'.format(
                self.dcc_file_name,
                ip_int,
                self.dcc_port,
                self.req.filesize,
                xdcc_token
            ),
            ctcp=True
        )

    def _parse_dcc_ip(self, raw_ip_str):
        """
        Safely convert a raw DCC integer string to a dotted-quad IPv4 string.
        Returns the IP string, or None if invalid or out of bounds.
        """
        try:
            raw_ip = int(raw_ip_str)
            if not (0 <= raw_ip <= 0xFFFFFFFF):
                return None
            return socket.inet_ntoa(struct.pack("!I", raw_ip))
        except (struct.error, ValueError, OverflowError):
            return None

    def process(self, pyfile):
        proto = self.info["pattern"]["PROTO"]
        server = unquote(self.info["pattern"]["SERVER"]).strip()
        chan = unquote(self.info["pattern"]["CHAN"]).strip()
        bot = unquote(self.info["pattern"]["BOT"]).strip()
        pack = self.info["pattern"]["PACK"].strip()

        # Enforce no CR, LF, or NULL bytes in URL components
        for name, val in (("SERVER", server), ("CHAN", chan), ("BOT", bot), ("PACK", pack)):
            if any(c in val for c in ("\r", "\n", "\0")):
                self.fail(self._("Invalid characters (CRLF/NULL) in URL component: {}").format(name))

        # Validate channel name (no spaces, control chars, colons, or commas)
        clean_chan = chan[1:] if chan.startswith("#") else chan
        if not clean_chan or any(c in clean_chan for c in (" ", ",", "\x07", ":")):
            self.fail(self._("Invalid IRC channel name in URL: {}").format(chan))

        # Validate bot nickname (alphanumeric and allowed IRC special characters)
        if not re.match(r"^[a-zA-Z0-9_\-\[\]\\^{}|`]+$", bot):
            self.fail(self._("Invalid IRC bot nickname in URL: {}").format(bot))

        tls_opts = [
            _x.split("/")
            for _x in self.config.get("tls_opts").strip().split(",")
            if len(_x.split("/")) == 3 and _x.split("/")[2].strip().lower() in ("true", "false", "starttls")
        ]

        #: Remove leading '#' from channel name
        for opt in tls_opts:
            opt[1] = opt[1][1:] if opt[1].startswith("#") else opt[1]
            opt[2] = opt[2].strip().lower()

        server_parts = server.split(":")

        if proto == "xdccs":
            use_ssl=IRC.SSLUsage.TRUE
        else:
            default_tls_mode = self.config.get("default_tls_mode")
            if default_tls_mode == "on":
                use_ssl = IRC.SSLUsage.TRUE
            elif default_tls_mode == "starttls":
                use_ssl = IRC.SSLUsage.STARTTLS
            else:
                use_ssl = IRC.SSLUsage.FALSE

            for opt in tls_opts:
                if (
                    opt[0].lower() == server_parts[0].lower()
                    and opt[1].lower() in ("*", chan.lower())
                ):
                    if opt[2].lower() == "true":
                        use_ssl = IRC.SSLUsage.TRUE
                    elif opt[2].lower() == "starttls":
                        use_ssl = IRC.SSLUsage.STARTTLS
                    else:
                        use_ssl = IRC.SSLUsage.FALSE
                    break

        ln = len(server_parts)
        if ln == 2:
            host, port = server_parts[0], int(server_parts[1])

        elif ln == 1:
            host, port = server_parts[0], 6697 if proto == "xdccs" or use_ssl == IRC.SSLUsage.TRUE else 6667

        else:
            self.fail(self._("Invalid hostname for IRC Server: {}").format(server))

        nick = self.config.get("nick")
        nick_pw = self.config.get("nick_pw")
        ident = self.config.get("ident")
        realname = self.config.get("realname")

        queued_timeout = self.config.get("queued_timeout") * 60
        queue_query_interval = self.config.get("queue_query_interval") * 60
        response_timeout = max(self.config.get("response_timeout"), 60)
        self.config.set("response_timeout", response_timeout)

        waiting_opts = [
            _x.split("/")
            for _x in self.config.get("waiting_opts").strip().split(",")
            if len(_x.split("/")) == 3 and _x.split("/")[2].isnumeric()
        ]

        #: Remove leading '#' from channel name
        for opt in waiting_opts:
            opt[1] = opt[1][1:] if opt[1].startswith("#") else opt[1]
            opt[2] = int(opt[2])

        invite_opts = [
            _x.split("/")
            for _x in self.config.get("invite_opts").strip().split(",")
            if len(_x.split("/")) == 4
        ]

        #: Remove leading '#' from channel name
        for opt in invite_opts:
            opt[1] = opt[1][1:] if opt[1].startswith("#") else opt[1]

        channel_opts = [
            _x.split("/")
            for _x in self.config.get("channel_opts").strip().split(",")
            if len(_x.split("/")) == 3
        ]

        #: Remove leading '#' from channel name and custom channel name
        for opt in channel_opts:
            opt[1] = opt[1][1:] if opt[1].startswith("#") else opt[1]
            opt[2] = opt[2][1:] if opt[2].startswith("#") else opt[2]

        #: Change request type
        self.req.close()
        self.req = self.pyload.request_factory.get_request(self.classname, request_type="XDCC")

        self.pyfile.set_custom_status("connect irc")

        self.irc_client = IRC(self, nick, ident, realname)

        for _ in range(3):
            try:
                if self.irc_client.connect_server(host, port, use_ssl=use_ssl):
                    try:
                        if nick_pw:
                            self.irc_client.nickserv_identify(nick_pw)

                        for opt in invite_opts:
                            if (
                                opt[0].lower() == host.lower()
                                and opt[1].lower() == chan.lower()
                            ):
                                self.irc_client.send_invite_request(
                                    opt[2], opt[1], opt[3]
                                )
                                break

                        for opt in channel_opts:
                            if (
                                opt[0].lower() == host.lower()
                                and opt[1].lower() == chan.lower()
                            ):
                                if not self.irc_client.join_channel(opt[2]):
                                    self.fail(self._("Cannot join channel"))

                        if not self.irc_client.join_channel(chan):
                            self.fail(self._("Cannot join channel"))

                        if not self.irc_client.is_bot_online(bot):
                            self.fail(self._("Bot is offline"))

                        for opt in waiting_opts:
                            if (
                                opt[0].lower() == host.lower()
                                and opt[1].lower() == chan.lower()
                                and opt[2] > 0
                            ):
                                self.wait(opt[2], reconnect=False)

                        self.pyfile.set_status("waiting")

                        self.irc_client.xdcc_request_pack(bot, pack)

                        # Main IRC loop
                        while (
                            not self.pyfile.abort or self.dl_started
                        ) and not self.dl_finished:
                            if not self.dl_started:
                                if self.queued_time:
                                    if (
                                        queued_timeout
                                        and time.monotonic() - self.queued_time
                                        > queued_timeout
                                    ):
                                        self.irc_client.xdcc_remove_queued(bot)
                                        self.queued_time = False
                                        self.irc_client.disconnect_server()
                                        self.log_error(
                                            self._(
                                                "Timed out while waiting in the XDCC queue ({} seconds)"
                                            ).format(queued_timeout)
                                        )
                                        self.retry(
                                            3,
                                            60,
                                            self._(
                                                "Timed out while waiting in the XDCC queue ({} seconds)"
                                            ).format(queued_timeout),
                                        )

                                    elif (
                                        queue_query_interval
                                        and time.monotonic()
                                        - self.irc_client.xdcc_queue_query_time
                                        > queue_query_interval
                                    ):
                                        self.irc_client.xdcc_query_queue_status(bot)

                                elif self.last_response_time:
                                    if (
                                        time.monotonic() - self.last_response_time
                                        > response_timeout
                                    ):
                                        self.irc_client.xdcc_request_pack(bot, pack)
                                        self.last_response_time = 0

                                else:
                                    if (
                                        self.irc_client.xdcc_request_time
                                        and time.monotonic()
                                        - self.irc_client.xdcc_request_time
                                        > response_timeout
                                    ):
                                        self.irc_client.disconnect_server()
                                        self.log_error(
                                            self._("XDCC Bot did not answer")
                                        )
                                        self.retry(
                                            3, 60, self._("XDCC Bot did not answer")
                                        )

                            origin, command, args = self.irc_client.get_irc_command()
                            self.process_irc_command(origin, command, args)

                            if self.last_exception:
                                raise self.last_exception

                    finally:
                        if (
                            self.pyfile.abort
                            and not self.dl_started
                            and self.queued_time
                        ):
                            self.irc_client.xdcc_remove_queued(bot)
                        self.irc_client.disconnect_server()

                return

            except socket.error as exc:
                if hasattr(exc, "errno") and exc.errno is not None:
                    err_no = exc.errno

                    if err_no in (10054, 10061):
                        self.log_warning("Server blocked our ip, retry in 5 min")
                        self.wait(300)
                        continue

                    else:
                        self.log_error(
                            self._("Failed due to socket errors. Code: {}").format(
                                err_no
                            )
                        )
                        self.fail(
                            self._("Failed due to socket errors. Code: {}").format(
                                err_no
                            )
                        )

                else:
                    err_msg = exc.args[0]
                    self.log_error(
                        self._("Failed due to socket errors: '{}'").format(err_msg)
                    )
                    self.fail(
                        self._("Failed due to socket errors: '{}'").format(err_msg)
                    )

        self.log_error(self._("Server blocked our ip, retry again later manually"))
        self.fail(self._("Server blocked our ip, retry again later manually"))

    def process_irc_command(self, origin, command, args):
        bot = self.info["pattern"]["BOT"]
        nick = self.config.get("nick")

        if origin is None or command is None or args is None:
            return

        #: ERR_CANTSENDTOUSER
        if (
            command == "531"
            and len(args) >= 3
            and args[0].casefold() == nick.casefold()
            and args[1].casefold() == bot.casefold()
        ):
            text = args[2]
            self.log_error("<{}> {}".format(bot, text))
            self.fail(text)

        # Private message from bot to us?
        bot_host = self.irc_client.get_bot_host(bot)
        if not self.irc_client.is_message_from_target(origin, command, args, bot, bot_host):
            return

        text = args[1]
        sender_nick = origin.split("@")[0].split("!")[0]
        self.log_debug(f"PrivMsg: <{sender_nick}> {text}")

        if not self.queued_time and text in (
            "You already requested that pack",
            "All Slots Full",
            "You have a DCC pending",
        ):
            self.last_response_time = time.monotonic()

        elif "you must be on a known channel to request a pack" in text:
            self.log_error(self._("Invalid channel"))
            self.fail(self._("Invalid channel"))

        elif "Invalid Pack Number" in text:
            self.log_error(self._("Invalid Pack Number"))
            self.fail(self._("Invalid Pack Number"))

        # Check for regular DCC SEND
        m = self.RE_XDCC.match(text)
        if m:
            self.dcc_port = int(m.group("PORT"))
            self.dcc_file_name = m.group("NAME")
            file_size = int(m.group("SIZE") or 0)
            self.dcc_sender_bot = origin.split("@")[0].split("!")[0]
            dcc_token = m.group("TOKEN")

            is_pasv_dcc = self.dcc_port == 0 and dcc_token != ""
            if is_pasv_dcc:
                self.log_debug(self._("Received **PASSIVE** XDCC SEND (unsecured) request"))
                listen_port = self.config.get("passive_port")
                if listen_port == 0:
                    self.fail(self._("Passive XDCC is disabled"))
                else:
                    self.dcc_port = listen_port
                    self.do_download_passive(self.dcc_port, int(dcc_token), self.dcc_file_name, file_size)

            else:
                self.log_debug(self._("Received XDCC SEND (unsecured) request"))
                ip = self._parse_dcc_ip(m.group("IP"))
                if not ip or not is_global_address(ip):
                    self.log_error(self._("Private or reserved IP addresses received from bot"))
                    self.fail(self._("Private or reserved IP addresses received from bot"))

                self.do_download(ip, self.dcc_port, False,  self.dcc_file_name, file_size)

        else:
            # Check for SSL DCC SSEND
            m = self.RE_XDCC_SSEND.match(text)
            if m:
                ip = self._parse_dcc_ip(m.group("IP"))
                if not ip or not is_global_address(ip):
                    self.log_error(self._("Private or reserved IP addresses received from bot"))
                    self.fail(self._("Private or reserved IP addresses received from bot"))

                self.dcc_port = int(m.group("PORT"))
                self.dcc_file_name = m.group("NAME")
                file_size = int(m.group("SIZE") or 0)
                self.dcc_sender_bot = origin.split("@")[0].split("!")[0]

                self.log_debug(self._("Received XDCC SSEND (Secure) request"))
                self.do_download(ip, self.dcc_port, True, self.dcc_file_name, file_size)

            else:
                m = self.RE_QUEUED.search(text)
                if m:
                    self.queued_time = self.last_response_time = time.monotonic()
                    self.log_info(self._("Got queued at position {}").format(m.group(1)))

                else:
                    m = self.RE_QUEUE_STAT.search(text)
                    if m:
                        self.log_info(
                            self._(
                                "Waiting in the queue for about {}, current position {}, estimated remaining wait time: {}"
                            ).format(
                                format.time(time.monotonic() - self.queued_time),
                                m.group(1),
                                m.group(2),
                            )
                        )

    def _on_notification(self, notification):
        if "progress" in notification:
            self.pyfile.set_progress(notification["progress"])

    @threaded
    def do_download(self, ip, port, use_ssl, file_name, file_size):
        if self.dl_started:
            return

        self.dl_started = True

        try:
            self.pyfile.name = file_name
            self.req.filesize = file_size

            self.pyfile.set_status("downloading")

            dl_folder = os.path.join(
                self.pyload.config.get("general", "storage_folder"),
                self.pyfile.package().folder
                if self.pyload.config.get("general", "folder_per_package")
                else "",
            )
            os.makedirs(dl_folder, exist_ok=True)
            self.set_permissions(dl_folder)

            self.check_duplicates()

            dl_file = os.path.join(dl_folder, self.pyfile.name)

            self.log_debug(
                self._("DOWNLOAD XDCC '{}' from {}:{}").format(file_name, ip, port)
            )

            self.pyload.addon_manager.dispatch_event(
                "download_start", self.pyfile, "{}:{}".format(ip, port), dl_file
            )

            newname = self.req.download(
                ip,
                port,
                dl_file,
                status_notify=self._on_notification,
                resume=self.xdcc_send_resume,
                use_ssl=use_ssl
            )
            if newname and newname != dl_file:
                self.log_info(
                    self._("{name} saved as {newname}").format(
                        name=self.pyfile.name, newname=newname
                    )
                )
                dl_file = newname

            self.last_download = dl_file

        except Abort:
            pass

        except Exception as exc:
            bot = self.info["pattern"]["BOT"]
            self.irc_client.xdcc_cancel_pack(bot)

            if not self.last_exception:
                self.last_exception = exc  #: pass the exception to the main thread

        self.dl_finished = True

    @threaded
    def do_download_passive(self, listen_port, dcc_token, file_name, file_size):
        if self.dl_started:
            return

        self.dl_started = True

        try:
            self.pyfile.name = file_name
            self.req.filesize = file_size

            self.pyfile.set_status("downloading")

            dl_folder = os.path.join(
                self.pyload.config.get("general", "storage_folder"),
                self.pyfile.package().folder
                if self.pyload.config.get("general", "folder_per_package")
                else "",
            )
            os.makedirs(dl_folder, exist_ok=True)
            self.set_permissions(dl_folder)

            self.check_duplicates()

            dl_file = os.path.join(dl_folder, self.pyfile.name)

            self.log_debug(
                self._("DOWNLOAD passive XDCC '{}' from bot {} (token {})").format(file_name, self.dcc_sender_bot, dcc_token)
            )

            self.pyload.addon_manager.dispatch_event(
                "download_start", self.pyfile, f"passive:{self.dcc_sender_bot}", dl_file
            )

            newname = self.req.download_passive(
                listen_port,
                dl_file,
                self.xdcc_initiate_passive,
                listen_host=self.pyload.config.get("webui", "host"),
                status_notify=self._on_notification,
                resume=self.xdcc_send_resume,
                dcc_token=dcc_token,
            )
            if newname and newname != dl_file:
                self.log_info(
                    self._("{name} saved as {newname}").format(
                        name=self.pyfile.name, newname=newname
                    )
                )
                dl_file = newname

            self.last_download = dl_file

        except Abort:
            pass

        except Exception as exc:
            bot = self.info["pattern"]["BOT"]
            self.irc_client.xdcc_cancel_pack(bot)

            if not self.last_exception:
                self.last_exception = exc  #: pass the exception to the main thread

        self.dl_finished = True
