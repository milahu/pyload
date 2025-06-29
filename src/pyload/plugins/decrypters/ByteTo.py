# -*- coding: utf-8 -*-

# based on src/pyload/plugins/decrypters/SerienfansOrg.py
# based on src/pyload/plugins/decrypters/SerienStreamTo.py

# Test links:
#   https://byte.to/?q=tarzan+raist
"""
<P CLASS="TITLE"><A HREF="/category/MicroHD/Tarzans-Todesduell-1963-German-800p-AC3-microHD-x264-RAIST-1157058.html">Tarzans Todesduell 1963 German 800p AC3 microHD x264 - RAIST</A></P>
<P CLASS="TITLE"><A HREF="/category/MicroHD/Tarzans-groesstes-Abenteuer-1959-German-1080p-AC3-microHD-x264-RAIST-1157057.html">Tarzans gr&ouml;&szlig;tes Abenteuer 1959 German 1080p AC3 microHD x264 - RAIST</A></P>
<P CLASS="TITLE"><A HREF="/category/MicroHD/Tarzan-erobert-Indien-1962-German-800p-AC3-microHD-x264-RAIST-1157056.html">Tarzan erobert Indien 1962 German 800p AC3 microHD x264 - RAIST</A></P>
"""
#   https://byte.to/category/MicroHD/Tarzans-Todesduell-1963-German-800p-AC3-microHD-x264-RAIST-1157058.html
"""
<th align="LEFT" width="75%" style="padding:5px">Mirror #1 von Raistlin911 | Passwort: keine Angabe</th>
<iframe frameBorder="0" src="https://byte.to/widgets/button.php?dmVrQys0OW1JczU3dEVwZTdkWTdGdGtTQno1dlJuL3h6OHExVkNQbS9KNzMzWEZHejJaVUtJNHZXZGU4aTc3VDZZQ3g5RWZqSVkzUGZVVkZ6bGwxTnc9PTo6jdI0yVFGpL3EZCOYWw57HQ==" style="height:35px;width:195px;margin-bottom:5px;margin-right:10px" align="left">loading ...</IFRAME>
<iframe frameBorder="0" src="https://byte.to/widgets/button.php?dmVrQys0OW1JczU3dEVwZTdkWTdGdGtTQno1dlJuL3h6OHExVkNQbS9KN1dBZXJUL3QxcXU1V3U2L1ZNcG5nUVAwQkpCVmlJZ0c3U3d2NmIyTXdqdmc9PTo6uY7ZFgumWqdRv9+bZQvtLQ==" style="height:35px;width:195px;margin-bottom:5px;margin-right:10px" align="left">loading ...</IFRAME>
"""
#   https://byte.to/widgets/button.php?dmVrQys0OW1JczU3dEVwZTdkWTdGdGtTQno1dlJuL3h6OHExVkNQbS9KNzMzWEZHejJaVUtJNHZXZGU4aTc3VDZZQ3g5RWZqSVkzUGZVVkZ6bGwxTnc9PTo6jdI0yVFGpL3EZCOYWw57HQ==
"""
<a href="https://byte.to/go.php?hash=dmVrQys0OW1JczU3dEVwZTdkWTdGdGtTQno1dlJuL3h6OHExVkNQbS9KNzMzWEZHejJaVUtJNHZXZGU4aTc3VDZZQ3g5RWZqSVkzUGZVVkZ6bGwxTnc9PTo6jdI0yVFGpL3EZCOYWw57HQ==" target="_blank" class="loadbutton"><span class="green-dot"></span> <img src='//www.google.com/s2/favicons?domain=rapidgator.net' title='rapidgator.net' /> rapidgator.net</a>
"""
#   https://byte.to/go.php?hash=dmVrQys0OW1JczU3dEVwZTdkWTdGdGtTQno1dlJuL3h6OHExVkNQbS9KNzMzWEZHejJaVUtJNHZXZGU4aTc3VDZZQ3g5RWZqSVkzUGZVVkZ6bGwxTnc9PTo6jdI0yVFGpL3EZCOYWw57HQ==
"""
HTTP/2 302 
location: https://www.filecrypt.cc/Container/1545CC0166.html
"""

import os
import re
import urllib.parse
import time

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__) + "/../../..")

from pyload.plugins.base.decrypter import BaseDecrypter
from pyload.core.network.http.exceptions import BadHeader


class Release:
    def __init__(self):
        self.name = None
        self.password = None
        self.urls = []


class ByteTo(BaseDecrypter):
    __name__ = "ByteTo"
    __type__ = "decrypter"
    __version__ = "0.1"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?byte\.to/.*"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("use_first_online_hoster_only", "bool", "Use first online hoster only", False),
    ]

    __description__ = """Byte.to decrypter plugin"""
    __license__ = "MIT"
    __authors__ = [
        ("milahu", "milahu@gmail.com"),
    ]

    def setup(self):
        self.urls = []
        self.releases = []

    def decrypt(self, pyfile):
        self.pyfile = pyfile
        self.pyfile_url_parsed = urllib.parse.urlparse(pyfile.url)

        self.releases = []

        if self.pyfile_url_parsed.path == '/' and 'q=' in self.pyfile_url_parsed.query:
            self._handle_search_query()
        # TODO handle "alternative search" queries like https://byte.to/search.php?title=tarzan+raist
        # elif self.pyfile_url_parsed.path == '/search.php':
        #     self._handle_search_query_2()
        elif re.match(r"/category/[^/]+/[^/]+\.html", self.pyfile_url_parsed.path):
            # https://byte.to/category/MicroHD/Tarzans-Todesduell-1963-German-800p-AC3-microHD-x264-RAIST-1157058.html
            # note: actual "category" links look like https://byte.to/?cat=12
            self._handle_release_page()
        else:
            self.log_error(f"ignoring not-supported url: {pyfile.url!r}")
            return

        # Create packages from found releases
        for release in self.releases:
            package_name = release.name
            if release.password:
                # TODO better: set package password
                package_name += f" (Password: {release.password})"

            self.packages.append((package_name, [url for _, url in release.urls], package_name))

    def _handle_search_query(self):
        """Handle search query URLs"""
        self.log_info(f"Processing search query: {self.pyfile.url}")

        # Get search results page
        html = self._get_response_text(self.pyfile.url)

        # Find all search results using regex
        # Pattern: <P CLASS="TITLE"><A HREF="(URL)">(TITLE)</A></P>
        results = re.findall(
            r'<P\s+CLASS="TITLE"><A\s+HREF="([^"]+)">([^<]+)</A></P>',
            html
        )

        if not results:
            self.log_error("No search results found")
            return
            
        for url, title in results:
            full_url = urllib.parse.urljoin(self.pyfile.url, url)
            # TODO decode title from html to utf8
            self.log_info(f"Found result: {title} -> {full_url}")
            self._handle_release_page(release_page_url=full_url)

    def _handle_release_page(self, release_page_url=None):
        """Handle release page URLs"""

        if not release_page_url:
            release_page_url = self.pyfile.url

        self.log_info(f"Processing release page: {release_page_url}")

        release_page_url_parsed = urllib.parse.urlparse(release_page_url)

        # Get release page
        html = self._get_response_text(release_page_url)

        # Create release object
        release = Release()

        # Get release title from URL if we can't find it in the page
        # https://byte.to/category/MicroHD/Tarzans-Todesduell-1963-German-800p-AC3-microHD-x264-RAIST-1157058.html
        release.name = os.path.basename(release_page_url_parsed.path)
        # Tarzans-Todesduell-1963-German-800p-AC3-microHD-x264-RAIST-1157058.html
        release.name = re.sub(r"-[0-9]+\.html$", "", release.name)
        # Tarzans-Todesduell-1963-German-800p-AC3-microHD-x264-RAIST
        release.name = release.name.replace("-", ".")
        # Tarzans.Todesduell.1963.German.800p.AC3.microHD.x264.RAIST
        release.name = re.sub(r"\.([^.]+)$", r"-\1", release.name)
        # Tarzans.Todesduell.1963.German.800p.AC3.microHD.x264-RAIST
        self.log_info(f"parsed release.name from url: {release.name!r}")

        # Try to find a better title in the page
        title_regex = r'<td class="release-title">\s*<b>([^<]+)</b>'
        title_match = re.search(title_regex, html)
        if title_match:
            release.name = title_match.group(1).strip()
            self.log_info(f"parsed release.name from html: {release.name!r}")

        # FIXME dont allow FilecryptCc to modify the release name
        # otherwise we get ugly release names:
        """
        good:
        Tarzans.Todesduell.1963.German.800p.microHD.x264-RAIST
        Tarzans.groesstes.Abenteuer.1959.German.1080p.microHD.x264-RAIST

        bad:
        F6218TRZNSTDSDLL-RPG
        F6218TRZNSTDSDLL-DDL
        F6217TRZNSGRSSTSBNTR-RPG
        F6217TRZNSGRSSTSBNTR-DDL
        """

        # Find password if available
        # Pattern: <th align="LEFT" width="75%" style="padding:5px">Mirror #1 von Raistlin911 | Passwort: SOME_PASSWORD</th>
        password_match = re.search(
            r'<th[^>]*>.*?Passwort:\s*([^\s<]+)\s*</th>',
            html,
            re.IGNORECASE
        )
        if password_match:
            p = password_match.group(1).strip()
            if p != "keine Angabe":
                release.password = p
                self.log_info(f"Found password: {release.password}")
            # else: no password

        # Find download iframes
        # Pattern: <iframe frameBorder="0" src="https://byte.to/widgets/button.php?BASE64_DATA" ...>
        iframe_matches = re.findall(
            r'<iframe\s[^>]*src="(https?://byte\.to/widgets/button\.php\?[^"]+)"',
            html
        )

        if not iframe_matches:
            self.log_error("Not found download iframes at {release_page_url!r}")
            return

        for iframe_url in iframe_matches:
            self.log_info(f"Processing iframe: {iframe_url}")

            # Get the button page that contains the actual download link
            button_html = self._get_response_text(iframe_url)

            # Find the download link
            # Pattern: <a href="https://byte.to/go.php?hash=BASE64_DATA" ...> ... <img ... title='HOSTER_NAME' ...>
            download_match = re.search(
                r'<a\s+href="(https?://byte\.to/go\.php\?hash=[^"]+)"[^>]*>.*?<img[^>]*title=\'([^\']+)\'',
                button_html,
                re.DOTALL
            )

            if not download_match:
                self.log_error("Not found download link at {iframe_url!r}")
                continue

            download_url = download_match.group(1)
            hoster_name = download_match.group(2)

            self.log_info(f"Found download link for {hoster_name!r}: {download_url!r}")

            # Resolve the final hoster URL
            try:
                hoster_url = self._resolve_hoster_url(download_url)
                if hoster_url:
                    release.urls.append((hoster_name, hoster_url))
                    self.log_info(f"Resolved hoster URL: {hoster_url}")

                    if self.config.get('use_first_online_hoster_only'):
                        break  # Stop after first successful hoster
                else:
                    self.log_error("Not found hoster_url at {download_url!r}")
            except Exception as e:
                self.log_error(f"Not found hoster_url at {download_url!r}: {str(e)}")
                continue

        self.log_info(f"adding release {release}")
        self.releases.append(release)

    def _get_response_text(self, url, retries=3):
        """Get response text with retries"""
        for attempt in range(retries):
            try:
                self.log_debug(f"Fetching URL (attempt {attempt + 1}): {url}")
                return self.load(url)
            except BadHeader as e:
                if attempt == retries - 1:
                    raise
                self.log_warning(f"Bad header, retrying... ({str(e)})")
                time.sleep(3)
            except Exception as e:
                if attempt == retries - 1:
                    raise
                self.log_warning(f"Error fetching URL, retrying... ({str(e)})")
                time.sleep(3)

    def _resolve_hoster_url(self, url):
        """Resolve the final hoster URL by following redirects"""
        self.log_debug(f"Resolving hoster URL: {url}")
        
        # Get just the headers to follow redirects
        headers = self.load(url, just_header=True, redirect=False)
        
        if 'location' not in headers:
            raise Exception("No redirect location found")
            
        hoster_url = headers['location']
        self.log_debug(f"Redirected to: {hoster_url}")
        
        return hoster_url


# TODO move this to some util.py
def _mock_decrypter(cls):
    import logging
    from pyload.core.managers.file_manager import FileManager
    from pyload.core.network.request_factory import RequestFactory
    #from pyload.core.network.request_factory import get_request
    pyload_config = {
        "general": {
            "ssl_verify": False, # Verify SSL certificates
        },
        "download": {
            "ipv6": True, # allow ipv6
            "interface": "", # Download interface to bind (IP Address)
            "limit_speed": None,
        },
        "proxy": {
            "enabled": False,
        },
    }
    class MockConfig:
        # def get_plugin(self, plugin, key):
        #     print("MockConfig.get_plugin", plugin, key)
        #     return None
        def get(self, scope, key):
            try:
                return pyload_config[scope][key]
            except KeyError:
                pass
            print("MockConfig.get", scope, key)
            return None
    class MockPyload:
        log = logging.getLogger(__name__)
        #debug = 1 # compact debug log
        debug = 2 # trace debug log
        config = MockConfig()
        tempdir = "/tmp/pyLoad" # pyload.tempdir
        def __init__(self):
            self.log.setLevel(logging.DEBUG)
            self.files = self.file_manager = FileManager(self)
            self.req = self.request_factory = RequestFactory(self)
        def _(self, *a, **k):
            # translator function?
            return a[0]
    mock_pyload = MockPyload()
    class MockPackage:
        password = None
    import pycurl
    class MockPyFile:
        url = "http://localhost:99999999/"
        id = 123
        # set status for check_status in pyload/plugins/base/hoster.py
        # pyload.core.datatypes.enums.DownloadStatus.STARTING = 7
        status = 7
        abort = False
        _ = mock_pyload._
        def __init__(
            # actually "manager" is pyload.files
            # self.files = self.file_manager = FileManager(self)
            # self, manager, id, url, name, size, status, error, pluginname, package, order
            self, *args, **kwargs
        ):
            if args:
                print("MockPyFile.__init__: args", args, kwargs)
                manager, id, url, name, size, status, error, pluginname, package, order = args
                self.id = id
                self.url = url
                self.name = name
                self.size = size
                self.status = status
            #self.m = self.manager = pycurl.CurlMulti() # no! this is FileManager
            #self.m = self.manager = manager
            self.m = self.manager = mock_pyload.files
            self._package = MockPackage()
        def package(self):
            return self._package
    def mock_init(self, *a, **k):
        mock_pyfile = MockPyFile()
        mock_pyload = MockPyload()
        self.pyload = mock_pyload
        self.pyfile = mock_pyfile
        self.config = dict()
        for config_item in self.__config__:
            key, _type, desc, default = config_item
            self.config[key] = default
        self.log_debug = lambda *a: print("debug:", *a)
        self.log_info = lambda *a: print("info:", *a)
        self.log_warning = lambda *a: print("warning:", *a)
        self.log_error = lambda *a: print("error:", *a)
    #cls.__init__ = mock_init
    pyfile = MockPyFile()
    decrypter = cls(pyfile)
    decrypter.log_debug = lambda *a: print("debug:", *a)
    decrypter.log_info = lambda *a: print("info:", *a)
    decrypter.log_warning = lambda *a: print("warning:", *a)
    decrypter.log_error = lambda *a: print("error:", *a)
    decrypter.config = dict()
    for config_item in decrypter.__config__:
        key, _type, desc, default = config_item
        decrypter.config[key] = default
    return decrypter


if __name__ == "__main__":
    # debug
    """
    examples:
    python src/pyload/plugins/decrypters/SerienfansOrg.py https://byte.to/category/MicroHD/Tarzans-Todesduell-1963-German-800p-AC3-microHD-x264-RAIST-1157058.html
    python src/pyload/plugins/decrypters/SerienfansOrg.py "https://byte.to/?q=tarzan+raist"
    """

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()

    decrypter = _mock_decrypter(ByteTo)

    # write cache files
    decrypter._write_cache = True
    # read cache files
    decrypter._read_cache = True

    pyfile = decrypter.pyfile
    pyfile.url = args.url

    decrypter.decrypt(pyfile)

    print("decrypter.packages", decrypter.packages)
