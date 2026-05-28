from pyload.webui.app.blueprints.cnl_blueprint import clicknload_decrypt2


if __name__ == "__main__":
    # python -m src.pyload.plugins.decrypters.ClickNLoad
    import sys
    jk = sys.argv[1]
    try:
        crypted = sys.argv[2]
    except IndexError:
        # read crypted from stdin
        crypted = sys.stdin.read().strip()
    links = clicknload_decrypt2(crypted, jk)
    print(f"decrypted {len(links)} links:", file=sys.stderr)
    for link in links:
        print(link)
