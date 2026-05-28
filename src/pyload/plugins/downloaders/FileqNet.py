from ..base.xfs_downloader import XFSDownloader


class FileqNet(XFSDownloader):
    __name__ = "FileqNet"
    __type__ = "downloader"
    __version__ = "0.02"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?fileq\.net/(?P<ID>\w{12})"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Fileq.net downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    PLUGIN_DOMAIN = "fileq.net"

    URL_REPLACEMENTS = [(__pattern__ + ".*", r"https://fileq.net/\g<ID>")]

    INFO_PATTERN = r'onfocus="copy\(this\)">\[URL=[^\]]+\](?P<N>.+?) -  (?P<S>\d+)'
