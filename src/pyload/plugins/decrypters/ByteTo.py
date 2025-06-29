# -*- coding: utf-8 -*-

#
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

# AI prompts for https://chat.deepseek.com/
"""
can you modify my python script?

---

Please share the script you'd like to modify
and let me know what changes or improvements you'd like to make.

---

the script is a plugin for the "pyload" download manager.
the script is based on a plugin for a different website.
this script should get downloads from the website byte.to.

the plugin can download html with
self._get_response_text

the plugin can resolve http redirects with
self._resolve_hoster_url

the plugin's main method is the "decrypt" method,
here the plugin gets a "pyfile" object
with the "pyfile.url" attribute.

"pyfile.url" can be one of:
1. a search query like "https://byte.to/?q=tarzan+raist"
2. a release page like "https://byte.to/category/MicroHD/Tarzans-Todesduell-1963-German-800p-AC3-microHD-x264-RAIST-1157058.html"

if "pyfile.url" is a search query,
the plugin should parse all search results, for example:
<P CLASS="TITLE"><A HREF="/category/MicroHD/Tarzans-Todesduell-1963-German-800p-AC3-microHD-x264-RAIST-1157058.html">Tarzans Todesduell 1963 German 800p AC3 microHD x264 - RAIST</A></P>
<P CLASS="TITLE"><A HREF="/category/MicroHD/Tarzans-groesstes-Abenteuer-1959-German-1080p-AC3-microHD-x264-RAIST-1157057.html">Tarzans gr&ouml;&szlig;tes Abenteuer 1959 German 1080p AC3 microHD x264 - RAIST</A></P>
<P CLASS="TITLE"><A HREF="/category/MicroHD/Tarzan-erobert-Indien-1962-German-800p-AC3-microHD-x264-RAIST-1157056.html">Tarzan erobert Indien 1962 German 800p AC3 microHD x264 - RAIST</A></P>

if "pyfile.url" is a release page,
the plugin should
1. look for a password, for example:
<th align="LEFT" width="75%" style="padding:5px">Mirror #1 von Raistlin911 | Passwort: SOME_PASSWORD</th>
2. parse all download links, for example:
<iframe frameBorder="0" src="https://byte.to/widgets/button.php?dmVrQys0OW1JczU3dEVwZTdkWTdGdGtTQno1dlJuL3h6OHExVkNQbS9KNzMzWEZHejJaVUtJNHZXZGU4aTc3VDZZQ3g5RWZqSVkzUGZVVkZ6bGwxTnc9PTo6jdI0yVFGpL3EZCOYWw57HQ==" style="height:35px;width:195px;margin-bottom:5px;margin-right:10px" align="left">loading ...</IFRAME>
<iframe frameBorder="0" src="https://byte.to/widgets/button.php?dmVrQys0OW1JczU3dEVwZTdkWTdGdGtTQno1dlJuL3h6OHExVkNQbS9KN1dBZXJUL3QxcXU1V3U2L1ZNcG5nUVAwQkpCVmlJZ0c3U3d2NmIyTXdqdmc9PTo6uY7ZFgumWqdRv9+bZQvtLQ==" style="height:35px;width:195px;margin-bottom:5px;margin-right:10px" align="left">loading ...</IFRAME>

the download links return "level 2" download links like
<a href="https://byte.to/go.php?hash=dmVrQys0OW1JczU3dEVwZTdkWTdGdGtTQno1dlJuL3h6OHExVkNQbS9KNzMzWEZHejJaVUtJNHZXZGU4aTc3VDZZQ3g5RWZqSVkzUGZVVkZ6bGwxTnc9PTo6jdI0yVFGpL3EZCOYWw57HQ==" target="_blank" class="loadbutton"><span class="green-dot"></span> <img src='//www.google.com/s2/favicons?domain=rapidgator.net' title='rapidgator.net' /> rapidgator.net</a>

the "level 2" download links return an HTTP redirect like
HTTP/2 302 
location: https://www.filecrypt.cc/Container/1545CC0166.html
this location (currently called "hoster_url") should be added to the final result array
currently this is done with
release.urls.append((hoster_name, hoster_url))

please use regular expressions instead of BeautifulSoup.
i already told you how the html looks like, for example
<P CLASS="TITLE"><A HREF="/category/MicroHD/Tarzans-Todesduell-1963-German-800p-AC3-microHD-x264-RAIST-1157058.html">Tarzans Todesduell 1963 German 800p AC3 microHD x264 - RAIST</A></P>
"""
# -*- coding: utf-8 -*-

import os
import re
import urllib.parse
import time

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__) + "/../../.."

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

        if self.pyfile_url_parsed.path == '/' and self.pyfile_url_parsed.query.startswith('q='):
            self._handle_search_query()
        else:
            self._handle_release_page()

        # Create packages from found releases
        for release in self.releases:
            package_name = release.name
            if release.password:
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
            self.log_info("No search results found")
            return
            
        for url, title in results:
            full_url = urllib.parse.urljoin(self.pyfile.url, url)
            self.log_info(f"Found result: {title} -> {full_url}")
            
            # Create a release for each result
            release = Release()
            release.name = title.strip()
            release.urls.append(('byte.to', full_url))
            self.releases.append(release)

    def _handle_release_page(self):
        """Handle release page URLs"""
        self.log_info(f"Processing release page: {self.pyfile.url}")
        
        # Get release page
        html = self._get_response_text(self.pyfile.url)
        
        # Create release object
        release = Release()
        
        # Get release title from URL if we can't find it in the page
        release.name = os.path.basename(self.pyfile_url_parsed.path)
        
        # Try to find a better title in the page
        title_match = re.search(r'<title>([^<]+)</title>', html)
        if title_match:
            release.name = title_match.group(1).strip()
        
        # Find password if available
        # Pattern: <th align="LEFT" width="75%" style="padding:5px">Mirror #1 von Raistlin911 | Passwort: SOME_PASSWORD</th>
        password_match = re.search(
            r'<th[^>]*>.*?Passwort:\s*([^\s<]+).*?</th>',
            html,
            re.IGNORECASE
        )
        if password_match:
            release.password = password_match.group(1)
            self.log_info(f"Found password: {release.password}")
        
        # Find download iframes
        # Pattern: <iframe frameBorder="0" src="https://byte.to/widgets/button.php?BASE64_DATA" ...>
        iframe_matches = re.findall(
            r'<iframe\s[^>]*src="(https?://byte\.to/widgets/button\.php\?[^"]+)"',
            html
        )
        
        if not iframe_matches:
            self.log_info("No download iframes found")
            return
            
        for iframe_url in iframe_matches:
            self.log_info(f"Processing iframe: {iframe_url}")
            
            # Get the button page that contains the actual download link
            button_html = self._get_response_text(iframe_url)
            
            # Find the download button/link
            # Pattern: <a href="https://byte.to/go.php?hash=BASE64_DATA" ...> ... <img ... title='HOSTER_NAME' ...>
            download_match = re.search(
                r'<a\s+href="(https?://byte\.to/go\.php\?hash=[^"]+)"[^>]*>.*?<img[^>]*title=\'([^\']+)\'',
                button_html,
                re.DOTALL
            )
            
            if not download_match:
                continue
                
            download_url = download_match.group(1)
            hoster_name = download_match.group(2)
            
            self.log_info(f"Found download link for {hoster_name}: {download_url}")
            
            # Resolve the final hoster URL
            try:
                hoster_url = self._resolve_hoster_url(download_url)
                if hoster_url:
                    release.urls.append((hoster_name, hoster_url))
                    self.log_info(f"Resolved hoster URL: {hoster_url}")
                    
                    if self.config.get('use_first_online_hoster_only'):
                        break  # Stop after first successful hoster
            except Exception as e:
                self.log_error(f"Failed to resolve hoster URL: {str(e)}")
                continue
        
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


if __name__ == "__main__":
    # For testing purposes
    import sys
    from pyload.core.network.request_factory import RequestFactory
    
    class MockPyFile:
        def __init__(self, url):
            self.url = url
            self.id = 123
            self.package = lambda: None
            setattr(self.package(), 'password', None)
    
    class MockPlugin:
        def __init__(self):
            self.pyload = type('MockPyload', (), {
                'req': RequestFactory(None),
                'config': type('MockConfig', (), {
                    'get': lambda *_: True
                })
            })()
            self.config = {'use_first_online_hoster_only': False}
            self.log_debug = print
            self.log_info = print
            self.log_warning = print
            self.log_error = print
    
    # Test with either a search URL or release page URL
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://byte.to/category/MicroHD/Tarzans-Todesduell-1963-German-800p-AC3-microHD-x264-RAIST-1157058.html"
    
    plugin = ByteTo(MockPyFile(test_url))
    plugin.__dict__.update(MockPlugin().__dict__)
    plugin.decrypt(plugin.pyfile)
    
    print("\nFound packages:")
    for name, links, folder in plugin.packages:
        print(f"\nPackage: {name}")
        for link in links:
            print(f"  - {link}")
