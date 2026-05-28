
#
# Test links:
#   http://filecrypt.cc/Container/64E039F859.html

import base64
import re
import urllib.parse
import time

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from pyload.core.network.http.exceptions import BadHeader
from pyload.core.network.http.http_request import HTTPRequest
from pyload.core.utils.convert import to_str

from ..anticaptchas.CoinHive import CoinHive
from ..anticaptchas.ReCaptcha import ReCaptcha
from ..anticaptchas.SolveMedia import SolveMedia
from ..anticaptchas.CutCaptcha import CutCaptcha
from ..anticaptchas.CircleCaptcha import CircleCaptcha
from ..anticaptchas.POWCaptchaFilecryptCc import POWCaptchaFilecryptCc as POWCaptcha

from ..base.decrypter import BaseDecrypter
from ..helpers import replace_patterns

from pyload.plugins.decrypters.ClickNLoad import clicknload_decrypt2


class FilecryptCc(BaseDecrypter):
    __name__ = "FilecryptCc"
    __type__ = "decrypter"
    __version__ = "0.52"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?filecrypt\.(?:cc|co)/Container/\w+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("handle_mirror_pages", "bool", "Handle Mirror Pages", True),
    ]

    __description__ = """Filecrypt.cc decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zapp-brannigan", "fuerst.reinje@web.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    COOKIES = [("filecrypt.cc", "lang", "en")]
    URL_REPLACEMENTS = [(r"filecrypt.co", "filecrypt.cc")]

    PACKAGE_NAME_PATTERN = r"<h2>([^<]+)</h2>"

    DLC_LINK_PATTERN = r'onclick="DownloadDLC\(\'(.+)\'\);">'

    # TODO remove. all these links are protected by captchas
    # so it is better to add links via clicknload (CNL)
    # <button id="055AC1A2EE" onclick="try{openLink(this.getAttribute('data-055ac1a2ee'), this);}"
    #   data-055ac1a2ee="591096EB26" class="download" target="_blank" title="Download"></button>
    WEBLINK_PATTERN = r"<button onclick=\"[\w\-]+?/\*\d+?\*/\('([\w/-]+?)',"

    # TODO how do they escape singlequotes in the package name?
    # "&apos;"? "&#39;"? "&#x27;"?
    # package name is the last argument to CNLPOP
    CNL_PATTERN = r"""CNLPOP\('([^']+)', '([^']+)', '([^']+)', '(.*?)'\);"""

    # FIXME where is: status, url, hoster
    MIRROR_PAGE_PATTERN = r'"[\w]*" href="(https?://(?:www\.)?filecrypt.cc/Container/\w+\.html\?mirror=\d+)">'
    OFFLINE_PATTERN = r">Not Found<"

    CAPTCHA_PATTERN = r"<h2>Security Check</h2>"
    INTERNAL_CAPTCHA_PATTERN = r'<img id="nc" .* src="(.+?)"'
    CIRCLE_CAPTCHA_PATTERN = r'<input type="image" src="(.+?)"'
    KEY_CAPTCHA_PATTERN = r"<script language=JavaScript src='(http://backs\.keycaptcha\.com/swfs/cap\.js)'"
    SOLVEMEDIA_CAPTCHA_PATTERN = r'<script type="text/javascript" src="(https?://api(?:-secure)?\.solvemedia\.com/papi/challenge.+?)"'
    CUTCAPTCHA_CAPTCHA_KEY_PATTERN = r'''\sCUTCAPTCHA_MISERY_KEY\s*=\s*["']([0-9a-f]{40})["']'''
    CUTCAPTCHA_API_KEY_PATTERN = r'''cutcaptcha\.net/captcha/([0-9a-zA-Z]+)\.js'''
    POW_CAPTCHA_PATTERN = r'''<div class="pow-captcha" id="pow-captcha" .*>\n'''

    CAPTCHA_PATTERNS = [
        POWCaptcha.POW_CHALLENGE_PATTERN,
        INTERNAL_CAPTCHA_PATTERN,
        CIRCLE_CAPTCHA_PATTERN,
        KEY_CAPTCHA_PATTERN,
        SOLVEMEDIA_CAPTCHA_PATTERN,
        CUTCAPTCHA_CAPTCHA_KEY_PATTERN,
    ]

    def setup(self):
        self.urls = []
        self.package_name = None

        try:
            self.req.http.close()
        except Exception:
            pass

        self.req.http = HTTPRequest(
            cookies=self.req.cj,
            options=self.pyload.request_factory.get_options(),
            limit=2_000_000,
        )

    def decrypt(self, pyfile):
        self.pyfile = pyfile
        pyfile.url = replace_patterns(pyfile.url, self.URL_REPLACEMENTS)

        self.data = self._filecrypt_load_url(pyfile.url)
        #self.log_info("self.data[:1000]", self.data[:1000])

        if re.search(self.OFFLINE_PATTERN, self.data):
            self.offline()

        self.log_info("handle_password_protection")
        self.handle_password_protection()

        self.site_with_links = self.handle_captcha(pyfile.url)
        #self.log_info("self.site_with_links", repr(self.site_with_links)[:1000])

        if self.site_with_links is None:
            # FIXME why? captcha should be solved
            self.log_info("retry_captcha")
            self.retry_captcha()

        elif self.site_with_links == "":
            self.log_info("retry")
            self.retry()

        if self.config.get("handle_mirror_pages"):
            self.handle_mirror_pages()

        package_name = self.package_name or self.get_package_name()

        for handle in (
            self.handle_CNL,
            self.handle_weblinks,
            self.handle_dlc_container,
        ):
            handle()
            if self.urls:
                self.packages = [
                    (package_name, self.urls, package_name)
                ]
                return

    def get_package_name(self):
        m = re.search(self.PACKAGE_NAME_PATTERN, self.site_with_links)
        if m:
            name = m.group(1).strip()
            if name:
                return name
        # keep the pyload package name
        return self.pyfile.package().name

    def handle_mirror_pages(self):
        if "mirror=" not in self.site_with_links:
            return

        mirror = re.findall(self.MIRROR_PAGE_PATTERN, self.site_with_links)

        self.log_info(self._("Found {} mirrors").format(len(mirror)))

        for i in mirror[1:]:
            self.site_with_links = self.site_with_links + self._filecrypt_load_url(i)

    def handle_password_protection(self):
        # <input type="text" name="password" id="p4assw0rt"  autofocus autocomplete="off" placeholder="Passwort eingeben">
        if (
            re.search(
                r'name="password" id="p4assw0rt"',
                self.data,
            )
            is None
            or
            re.search(
                r'<!--\s*<input[^>]+name="password" id="p4assw0rt"',
                self.data,
            )
        ):
            self.log_info("not found password input")
            return

        self.log_info(self._("Folder is password protected"))

        password = self.get_password()

        if not password:
            self.fail(
                self._("Please enter the password in package section and try again")
            )

        # <input type="text" name="password" id="p4assw0rt"  autofocus autocomplete="off" placeholder="Passwort eingeben">
        self.data = self._filecrypt_load_url(
            self.pyfile.url, post={"password": password}
        )

    def search_captcha(self, html):
        for pattern in self.CAPTCHA_PATTERNS:
            if match := re.search(pattern, html, flags=re.DOTALL):
                self.log_info("search_captcha: found captcha", repr(match.group(0)))
                return True
        return False

    def handle_captcha(self, submit_url):
        if self.search_captcha(self.data):
            for handle in (
                self._handle_pow_captcha,
                self._handle_internal_captcha,
                self._handle_circle_captcha,
                self._handle_solvemedia_captcha,
                self._handle_keycaptcha_captcha,
                self._handle_coinhive_captcha,
                self._handle_recaptcha_captcha,
                self._handle_cutcaptcha_captcha,
            ):
                res = handle(submit_url)
                # res: html code
                if res is None:
                    continue
                elif res == "":
                    return res
                if self.search_captcha(res):
                    self.log_info("found another captcha in res")
                    return None

                else:
                    return res

            else:
                self.log_warning(self._("Unknown captcha found, retrying"))
                return ""

        else:
            self.log_info(self._("No captcha found"))
            return self.data

    def _handle_pow_captcha(self, url):
        retry_max = 10
        data = self.data
        self.captcha = POWCaptcha(self.pyfile)
        for retry_idx in range(retry_max):
            m = re.search(POWCaptcha.POW_CHALLENGE_PATTERN, data, flags=re.DOTALL)
            if not m:
                if retry_idx == 0:
                    self.log_error("POWCaptcha: Not found POW_CHALLENGE_PATTERN")
                    return None
                else:
                    # solved captchas
                    return data
            if retry_idx > 0:
                self.log_debug(f"POWCaptcha: try {retry_idx + 1} of {retry_max}")
            # the user has to click the captcha
            # to start the POW calculation
            time.sleep(2)
            params = self.captcha.challenge(data)
            data = self._filecrypt_load_url(url, post=params)
        # no. this is handled in "def handle_captcha"
        # else:
        #     # reached retry_max
        #     m = re.search(POWCaptcha.POW_CHALLENGE_PATTERN, data, flags=re.DOTALL)
        #     if m:
        #         # failed to solve captcha
        return data

    def _handle_internal_captcha(self, url):
        m = re.search(self.INTERNAL_CAPTCHA_PATTERN, self.data)
        if m is None:
            return
        captcha_url = urllib.parse.urljoin(self.pyfile.url, m.group(1))

        self.log_debug(f"Internal Captcha URL: {captcha_url}")

        captcha_code = self.captcha.decrypt(captcha_url, input_type="gif")

        return self._filecrypt_load_url(
            url, post={"recaptcha_response_field": captcha_code}
        )

    def _handle_circle_captcha(self, url):
        m = re.search(self.CIRCLE_CAPTCHA_PATTERN, self.data)
        if m is None:
            return
        # Please click into the open circle to continue.
        self.log_debug(
            "Circle Captcha URL: {}".format(
                urllib.parse.urljoin(self.pyfile.url, m.group(1))
            )
        )
        captcha_url = urllib.parse.urljoin(self.pyfile.url, m.group(1))
        self.log_debug(f"Circle Captcha URL: {captcha_url}")
        captcha_image = self._filecrypt_load_url(captcha_url, decode=False)
        self.captcha = CircleCaptcha(self.pyfile)
        captcha_coords = self.captcha.challenge(captcha_image)
        return self._filecrypt_load_url(
            # TODO parse dynamic input name: "button" or "buttonx" or ...
            #url, post={"button.x": captcha_coords[0], "button.y": captcha_coords[1]}
            url, post={"buttonx.x": captcha_coords[0], "buttonx.y": captcha_coords[1]}
        )

    def _handle_solvemedia_captcha(self, url):
        m = re.search(self.SOLVEMEDIA_CAPTCHA_PATTERN, self.data)
        if m is None:
            return
        self.log_debug(
            "Solvemedia Captcha URL: {}".format(
                urllib.parse.urljoin(self.pyfile.url, m.group(1))
            )
        )

        solvemedia = SolveMedia(self.pyfile)
        captcha_key = solvemedia.detect_key()

        if captcha_key:
            self.captcha = solvemedia
            response, challenge = solvemedia.challenge(captcha_key)

            return self._filecrypt_load_url(
                url,
                post={"adcopy_response": response, "adcopy_challenge": challenge},
            )

    def _handle_keycaptcha_captcha(self, url):
        m = re.search(self.KEY_CAPTCHA_PATTERN, self.data)
        if m is None:
            return
        self.log_debug(
            "Keycaptcha Captcha URL: {} unsupported, retrying".format(m.group(1))
        )
        return ""

    def _handle_coinhive_captcha(self, url):
        coinhive = CoinHive(self.pyfile)

        coinhive_key = coinhive.detect_key()
        if coinhive_key:
            self.captcha = coinhive
            token = coinhive.challenge(coinhive_key)

            return self._filecrypt_load_url(url, post={"coinhive-captcha-token": token})

        else:
            return None

    def _handle_recaptcha_captcha(self, url):
        recaptcha = ReCaptcha(self.pyfile)
        captcha_key = recaptcha.detect_key()

        if captcha_key:
            self.captcha = recaptcha
            response = recaptcha.challenge(captcha_key)

            return self._filecrypt_load_url(
                url, post={"g-recaptcha-response": response}
            )

        else:
            return None

    def _handle_cutcaptcha_captcha(self, url):
        # based on jdownloader
        # src/org/jdownloader/captcha/v2/challenge/cutcaptcha/AbstractCaptchaHelperCutCaptcha.java
        m = re.search(self.CUTCAPTCHA_CAPTCHA_KEY_PATTERN, self.data)
        if not m:
            return None
        captcha_key = m.group(1)
        m = re.search(self.CUTCAPTCHA_API_KEY_PATTERN, self.data)
        if not m:
            self.log_error("Cutcaptcha: Not found CUTCAPTCHA_API_KEY_PATTERN")
            return None
        api_key = m.group(1)
        # jd: CutCaptchaChallenge(plugin, siteKey, apiKey)
        self.captcha = CutCaptcha(self.pyfile)
        captcha_token = self.captcha.challenge(captcha_key, api_key)
        self.log_debug(f"Cutcaptcha: captcha_token={captcha_token}")
        return self._filecrypt_load_url(url, post={"cap_token": captcha_token})

    def handle_dlc_container(self):
        m = re.search(r"const (\w+) = DownloadDLC;", self.site_with_links)
        if m is not None:
            self.site_with_links = self.site_with_links.replace(m.group(1), "DownloadDLC")
        dlcs = re.findall(self.DLC_LINK_PATTERN, self.site_with_links)

        if not dlcs:
            return

        for dlc in dlcs:
            self.urls.append(
                urllib.parse.urljoin(self.pyfile.url, "/DLC/{}.dlc".format(dlc))
            )

    def handle_weblinks(self):
        try:
            links = re.findall(self.WEBLINK_PATTERN, self.site_with_links)

            for link in links:
                link = "https://filecrypt.cc/Link/{}.html".format(link)
                for i in range(5):
                    self.data = self._filecrypt_load_url(link)
                    m = re.search(r'https://filecrypt\.cc/index\.php\?Action=Go&id=\w+', self.data)
                    if m is not None:
                        headers = self._filecrypt_load_url(m.group(0), just_header=True)
                        url = headers["location"]
                        url = url.replace("\x10", "") # remove "Data Link Escape" chars
                        self.urls.append(url)
                        break

                else:
                    self.log_error(self._("Weblink could not be found"))

        except Exception as exc:
            self.log_debug(f"Error decrypting weblinks: {exc}")

    def handle_CNL(self):
        # based on https://filecrypt.cc/helper.html
        try:
            m = re.search(r"const (\w+) = CNLPOP;", self.site_with_links)
            if m is not None:
                self.site_with_links = self.site_with_links.replace(m.group(1), "CNLPOP")

            cnl_data_list = re.findall(
                self.CNL_PATTERN,
                self.site_with_links,
            )
            for cnl_data in cnl_data_list:
                # jk = cnl_data[0] # jk return value: "A397C71436" # noise?
                key_hexstr = cnl_data[1] # 32 char hex string
                assert len(key_hexstr) == 32, f"bad key_hexstr: {key_hexstr!r}"
                assert re.fullmatch(r"[0-9a-fA-F]+", key_hexstr), f"bad key_hexstr: {key_hexstr!r}"
                crypted = cnl_data[2] # long base64 string
                # NOTE self.package_name is the package name of the last cnl_data
                # but usually there is only one cnl_data
                if cnl_data[3]:
                    self.package_name = cnl_data[3]
                links = clicknload_decrypt2(crypted, key_hexstr)
                self.urls.extend(links)

        except Exception as exc:
            self.log_debug(f"Error decrypting CNL: {type(exc).__name__}: {exc}")

    def _filecrypt_load_url(self, *args, **kwargs):
        try:
            return self.load(*args, **kwargs)
        except BadHeader as exc:
            if exc.code == 500:
                return exc.content
            else:
                raise
