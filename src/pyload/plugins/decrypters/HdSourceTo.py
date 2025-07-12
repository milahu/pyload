# -*- coding: utf-8 -*-
# based on src/pyload/plugins/decrypters/SerienfansOrg.py
# based on src/pyload/plugins/decrypters/SerienStreamTo.py
# based on src/pyload/plugins/decrypters/ByteTo.py

# Test links:
#   https://hd-source.to/serien/spongebob-schwammkopf-s01-s13-complete-german-dl-1080p-web-h264-scene/
#   https://hd-source.to/category/filme/imdbtop250/
#   https://hd-source.to/?s=spongebob+schwammkopf

# AI prompt for https://chat.deepseek.com/
"""
can you write a pyload plugin?

i want to scrape download links from hd-source.to

the plugin should first check which type of URL was passed: search, category, imdb list, release page

then it should parse that page and use a regex to find links to next pages

all pages ultimately lead to release pages with download links like https://filecrypt.cc/Container/2663DAB669.html

i have added example html in the comments

here is my draft:
...
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


class HdSourceToZZZZZZZZZ(BaseDecrypter):
    __name__ = "HdSourceTo"
    __type__ = "decrypter"
    __version__ = "0.1"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?hd-source\.to/.*"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        # ("use_premium", "bool", "Use premium account if available", True),
        # ("use_first_online_hoster_only", "bool", "Use first online hoster only", False),
    ]

    __description__ = """HD-Source.to decrypter plugin"""
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
        elif re.match(r"/category/[^/]+/[^/]+\.html", self.pyfile_url_parsed.path):
            # https://byte.to/category/MicroHD/Tarzans-Todesduell-1963-German-800p-AC3-microHD-x264-RAIST-1157058.html
            # note: actual "category" links look like https://byte.to/?cat=12
            self._handle_release_page()
        else:
            self.log_error(f"ignoring not-supported url: {pyfile.url!r}")
            return

        self.pyfile.package().password = "hd-source.to"

        # Create packages from found releases
        for release in self.releases:
            self.packages.append((release.name, [url for _, url in release.urls], release.name))

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


class HdSourceTo(BaseDecrypter):
    __name__ = "HdSourceTo"
    __type__ = "decrypter"
    __version__ = "0.1"
    __status__ = "testing"

    __pattern__ = r"https?://(?:(?:www|xxx)\.)?hd-source\.to/.*"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", False),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
        ("include_filter", "str", "File extensions to include (separated by comma)", ""),
        ("exclude_filter", "str", "File extensions to exclude (separated by comma)", ""),
    ]

    __description__ = """HD-Source.to decrypter plugin"""
    __license__ = "MIT"
    __authors__ = [
        ("milahu", "milahu@gmail.com"),
    ]

    # https://hd-source.to/category/filme/imdbtop250/
    # <h2 class="entry-title"> <a href="https://hd-source.to/filme/fuer-ein-paar-dollar-mehr-1965-german-dtshd-720p-bluray-x264-veritas/"> Fuer.ein.paar.Dollar.mehr.1965.German.DTSHD.720p.BluRay.x264-Veritas </a></h2>
    # <h2 class="entry-title"> <a href="https://hd-source.to/filme/fuer-ein-paar-dollar-mehr-1965-german-ac3-dl-1080p-bluray-x265-veritas/"> Fuer.ein.paar.Dollar.mehr.1965.German.AC3.DL.1080p.BluRay.x265-Veritas </a></h2>
    # <h2 class="entry-title"> <a href="https://hd-source.to/filme/fuer-ein-paar-dollar-mehr-1965-german-dtshd-1080p-bluray-x264-veritas/"> Fuer.ein.paar.Dollar.mehr.1965.German.DTSHD.1080p.BluRay.x264-Veritas </a></h2>
    # https://hd-source.to/?s=spongebob+schwammkopf
    # <h2 class="entry-title"> <span class="blog-post-meta"> 13.10.21, 21:30 <span class="sep"> · </span> </span> <a href="https://hd-source.to/filme/spongebob-schwammkopf-schwamm-aus-dem-wasser-the-spongebob-movie-sponge-out-of-water-2015-multi-complete-bluray-internal-lieferdienst/"> SpongeBob.Schwammkopf.Schwamm.aus.dem.Wasser.The.SpongeBob.Movie.Sponge.Out.of.Water.2015.MULTi.COMPLETE.BLURAY.iNTERNAL-LiEFERDiENST </a></h2>
    # <h2 class="entry-title"> <span class="blog-post-meta"> 28.09.23, 1:27 <span class="sep"> · </span> </span> <a href="https://hd-source.to/filme/spongebob-schwammkopf-schwamm-aus-dem-wasser-2015-german-dl-1080p-bluray-x264-exquisite/"> SpongeBob.Schwammkopf.Schwamm.aus.dem.Wasser.2015.German.DL.1080p.BluRay.x264-EXQUiSiTE </a></h2>
    release_links_regex = r'<h2\s+class="entry-title"[^>]*>\s*.*?<a\s+href="([^"]+)"[^>]*>([^<]+)</a>'

    # https://hd-source.to/imdb-top-250/
    # 001. <a href="https://hd-source.to/?s=tt0111161" target="_blank">Die Verurteilten (1994)</a>
    # 002. <a href="https://hd-source.to/?s=tt0068646" target="_blank">Der Pate (1972)</a>
    # 003. <a href="https://hd-source.to/?s=tt0468569" target="_blank">The Dark Knight (2008)</a>
    movie_links_regex = r'<a\s+href="([^"]+)"\s+target="_blank"[^>]*>([^<]+)</a>'

    # https://hd-source.to/serien/spongebob-schwammkopf-s01-s13-complete-german-dl-1080p-web-h264-scene/
    # ignore links starting with "https://hd-source.to/out/af.php"
    # <a class="hosterlnk" title="Download via FileCrypt" href="https://hd-source.to/out/af.php?v=crypt1-671e2e930d059" target="_blank">
    # <a class="hosterlnk" title="Download via FileCrypt" href="https://filecrypt.cc/Container/2663DAB669.html" target="_blank">
    # <a class="hosterlnk" title="Download via FileCrypt" href="https://filecrypt.cc/Container/A913715A55.html" target="_blank">
    # <a class="hosterlnk" title="Download via FileCrypt" href="https://filecrypt.cc/Container/37398DA571.html" target="_blank">
    # download_links_regex = r'<a\s+class="hosterlnk"[^>]*href="(https?://(?!hd-source\.to/out/af\.php)[^"]+)"'
    # https://hd-source.to/serien/utopia-2020-s01-complete-german-dl-720p-web-h264-wvf/
    # <strong>Download:</strong> <a href="https://filecrypt.cc/Container/713F078662.html"  target="_blank">DDownload.com </a></font>
    # <strong>Mirror #1:</strong> <a href="https://filecrypt.cc/Container/81F6CD8A82.html"  target="_blank">Rapidgator.net </a></font>
    # download_links_regex = r'<a\s+class="hosterlnk"[^>]*href="(https?://[^"]+)"'
    # TODO more hosters
    download_links_regex = r'\s+href="(https://filecrypt.cc/Container/[^"]+)"'

    # <strong>Passwort: </strong>hd-source.to</p>
    release_password_regex = r'<strong>Passwort:\s*</strong>\s*([^<]+)</p>'

    release_title_regex = r'<h2 class="entry-title">([^<]+)</h2>'

    # https://hd-source.to/category/filme/imdbtop250/
    # <a class="next page-numbers" href="https://hd-source.to/category/filme/imdbtop250/page/2/"><i class="fa fa-angle-double-right"></i></a>
    # https://hd-source.to/?s=spongebob+schwammkopf
    # <a class="next page-numbers" href="https://hd-source.to/page/2/?s=spongebob+schwammkopf"><i class="fa fa-angle-double-right"></i></a>
    next_page_link_regex = r'<a\s+class="[^"]*next page-numbers[^"]*"\s+href="([^"]+)"'

    def setup(self):
        self.urls = []
        self.releases = []
        self.page_count = 0
        # TODO move to __config__, default 0
        self.max_pages = 20  # Safety limit for pagination

    def decrypt(self, pyfile):
        self.pyfile = pyfile
        self.pyfile_url_parsed = urllib.parse.urlparse(pyfile.url)

        self.releases = []
        self.page_count = 0

        path0 = self.pyfile_url_parsed.path.split('/', 2)[1]

        # TODO detect page type from html content, not from URL

        path0_list_category_page = (
            # https://hd-source.to/category/filme/imdbtop250/
            'category',
            # https://hd-source.to/formate/1080p/
            'formate',
            # https://hd-source.to/collection/collection/
            'collection',
            # https://hd-source.to/genres/documentary/
            'genres',
            # https://hd-source.to/imdb/9/
            'imdb',
            # https://hd-source.to/erscheinungsjahr/2024/
            'erscheinungsjahr',
        )

        path0_list_release_page = (
            # https://hd-source.to/filme/wunderschoener-2025-german-1080p-bluray-x264-gma/
            'filme',
            # https://hd-source.to/serien/spongebob-schwammkopf-s01-s13-complete-german-dl-1080p-web-h264-scene/
            'serien',
            # https://hd-source.to/spiele/tom-clancys-rainbow-six-siege-operation-wind-bastion-plaza/
            'spiele',
            # https://xxx.hd-source.to/xxx/tadpolexstudio-25-07-04-lilith-grace-makes-tad-pole-cum-twice-xxx-1080p-mp4-fetish/
            'xxx',
        )

        # Determine URL type and process accordingly
        if path0 == '' and self.pyfile_url_parsed.query.startswith('s='):
            # https://hd-source.to/?s=spongebob+schwammkopf
            # https://hd-source.to/?s=tt0111161
            self._handle_search_page()
        # TODO
        # elif self.pyfile_url_parsed.path == '/filter/' and self.pyfile_url_parsed.query != '':
        #     # https://hd-source.to/filter/?...
        #     self._handle_filter_search_page()
        # TODO
        # elif path0 == 'page':
        #     # https://hd-source.to/page/2/?s=1080p
        elif path0 in path0_list_category_page:
            self._handle_category_page()
        elif path0 == 'imdb-top-250':
            # https://hd-source.to/imdb-top-250/
            self._handle_imdb_list_page()
        elif path0 in path0_list_release_page:
            self._handle_release_page()
        else:
            self.log_error(f"FIXME detect page type from html content: {self.pyfile.url}")
            self.error("FIXME detect page type from html content")

        # Create packages from found releases
        for release in self.releases:
            if release.urls:
                self.packages.append((
                    release.name,
                    [url for _, url in release.urls],
                    release.name
                ))

    def _handle_search_page(self):
        """Handle search result pages"""
        self.log_info(f"Processing search page: {self.pyfile.url}")
        html = self.load(self.pyfile.url)

        # Find all release links in search results
        release_links = re.findall(self.release_links_regex, html, re.DOTALL)

        for url, title in release_links:
            full_url = urllib.parse.urljoin(self.pyfile.url, url)
            self.log_info(f"Found release: {title.strip()} -> {full_url}")
            self._handle_release_page(full_url)

        # Handle pagination
        self._handle_pagination(html)

    def _handle_category_page(self):
        """Handle category pages"""
        self.log_info(f"Processing category page: {self.pyfile.url}")
        html = self.load(self.pyfile.url)

        # Find release links in category pages (same pattern as search results)
        release_links = re.findall(self.release_links_regex, html, re.DOTALL)

        for url, title in release_links:
            full_url = urllib.parse.urljoin(self.pyfile.url, url)
            self.log_info(f"Found release: {title.strip()} -> {full_url}")
            self._handle_release_page(full_url)

        # Handle pagination
        self._handle_pagination(html)

    def _handle_imdb_list_page(self):
        """Handle the main IMDB Top 250 list page"""
        self.log_info(f"Processing IMDB list page: {self.pyfile.url}")
        html = self.load(self.pyfile.url)

        # Find movie links in the IMDB Top 250 list
        movie_links = re.findall(self.movie_links_regex, html)

        for url, title in movie_links:
            full_url = urllib.parse.urljoin(self.pyfile.url, url)
            self.log_info(f"Found movie: {title.strip()} -> {full_url}")

            # # The movie link goes to a search page, handle it accordingly
            # if '?s=' in full_url:
            #     self._handle_search_page(full_url)

    def _handle_release_page(self, release_page_url=None):
        """Handle individual release pages with download links"""
        if not release_page_url:
            release_page_url = self.pyfile.url

        self.log_info(f"Processing release page: {release_page_url}")
        html = self.load(release_page_url)

        # Create release object
        release = Release()

        # Get release name from page title
        title_match = re.search(self.release_title_regex, html)
        if title_match:
            release.name = title_match.group(1).strip()
            self.log_info(f"Release name: {release.name}")

        # Find password if available
        password_match = re.search(self.release_password_regex, html, re.IGNORECASE)
        if password_match:
            p = password_match.group(1).strip()
            if p.lower() not in ('keine', 'keine angabe', 'none'):
                release.password = p
                self.log_info(f"Found password: {release.password}")

        # Find all download links
        # We want FileCrypt links but skip the affiliate redirect links
        download_links = re.findall(self.download_links_regex, html)

        for url in download_links:
            if url.startswith('https://hd-source.to/out/af.php'):
                continue
            hoster = ''
            release.urls.append((hoster, url))

        if release.urls:
            self.releases.append(release)
        else:
            self.log_warning(f"No valid download links found on {release_page_url}")

    def _handle_pagination(self, html):
        """Handle pagination links if they exist"""
        # TODO parse page_count from url
        self.page_count += 1
        if self.max_pages > 0 and self.page_count >= self.max_pages:
            self.log_info("Reached maximum page limit, stopping pagination")
            return
        next_page_match = re.search(self.next_page_link_regex, html)
        if not next_page_match:
            return
        next_page_url = next_page_match.group(1)
        self.log_info(f"Found next page: {next_page_url}")
        if not 'hd-source.to/' in next_page_url:
            return
        pyfile = PyFile()
        pyfile.url = next_page_url
        self.decrypt(pyfile)


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
    python src/pyload/plugins/decrypters/HdSourceTo.py https://hd-source.to/serien/spongebob-schwammkopf-s14-complete-german-dl-720p-web-h264-wvf/
    python src/pyload/plugins/decrypters/HdSourceTo.py "https://hd-source.to/?s=spongebob+schwammkopf"
    """

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()

    decrypter = _mock_decrypter(HdSourceTo)

    # write cache files
    decrypter._write_cache = True
    # read cache files
    decrypter._read_cache = True

    pyfile = decrypter.pyfile
    pyfile.url = args.url

    decrypter.decrypt(pyfile)

    print("decrypter.packages", decrypter.packages)
