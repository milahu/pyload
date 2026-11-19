# Python filename encoding analysis

**User:** Anonymous  
**Created:** 2026/11/19 11:54:22  
**Updated:** 2026/11/19 14:13:26  
**Exported:** 2026/11/19 15:54:13  
**Link:** [<https://chatgpt.com/c/6afed55d-e4ec-83ed-82f5-666adaaef32b>](https://chatgpt.com/c/6afed55d-e4ec-83ed-82f5-666adaaef32b)

## Prompt:

11/19/2026, 11:54:21 AM

in python, why does it make my program hang when i write this string to the logger:

    'DÐ\x9e_Flair_and_MÐ¡-IÐ¡_-_Rollers_EP-(OIA90)-WEB-FLAC-2025.rar'

my quickfix is to use python's builtin "repr" function to escape all nonprintable characters.

but this is in pyload (the download manager), so another problem here is that the downloaded file is not written to disk.

i have tried to find files with "OIA90" in their filename, but such files dont exist.

what are some other possible filenames that could result from writing data to disk with such a nonprintable filename?

because pyload did not throw an error writing the downloaded file, pyload only crashed at logging the link status "Download finished: DÐ".

so either pyload used a different filename, or pyload failed silently to write the file

## Response:

11/19/2026, 11:54:28 AM

> **Searched 2 websites**
>
> Worked for 6s

The most important clue is that your filename appears to contain **mojibake (text decoded using the wrong character encoding)**, rather than genuinely nonprintable characters.

Your string:

looks like it was originally a filename containing Cyrillic characters, encoded as UTF-8 but subsequently interpreted as Latin-1 or Windows-1252.

This could explain the logging problem, but it doesn't necessarily explain the missing file.

## 1. What the original filename probably was

The suspicious sequences are:

| Corrupted text | Likely UTF-8 bytes | Original character       |
|----------------|--------------------|--------------------------|
| `Ð\x9e`        | `D0 9E`            | `О` (Cyrillic capital O) |
| `Ð¡`           | `D0 A1`            | `С` (Cyrillic capital S) |

The second character is visually similar to Latin `C`, but it is actually Cyrillic `С`.

Your original filename may therefore have been:

Notice that this is not the same as:

The first contains Cyrillic letters, whereas the second uses Latin letters.

You can attempt to recover the original string using:

If pyLoad is running on Linux with a UTF-8 filesystem locale, the recovered Cyrillic filename would be perfectly valid.

## 2. Why logging might crash

`\x9e` is a C1 control character (U+009E), not a valid printable character in ordinary Unicode text.

If the logging output is configured with a legacy encoding, or passes through a terminal, web interface, or other component that cannot handle that character, you may encounter encoding exceptions.

However, **Python's standard `logging` module should not normally hang merely because a string contains `\x9e`**.

A hang or crash suggests something else is happening, such as:

- An exception in the logging handler or output stream.
- A bug in pyLoad's logging or web interface.
- A Unicode encoding error that propagates through pyLoad's download completion code.
- A blocked output stream or logging handler.

Also, `repr()` doesn't escape every non-ASCII character. If your goal is ASCII-only logging, `ascii()` is more appropriate:

That makes the representation safe for an ASCII-only logging destination, although it doesn't fix the underlying filename encoding.

## 3. Other possible filenames to search for

There are several possibilities, depending on where the encoding corruption happened.

| Possibility | Filename prefix |
|----|----|
| Original Cyrillic | `DО_Flair_and_MС-IС_` |
| Corrupted Latin-1 | `DÐ\x9e_Flair_and_MÐ¡-IÐ¡_` |
| Latin transliteration | `DO_Flair_and_MC-IC_` |
| Replacement characters | `D�_Flair_and_M�-I�_` |
| Removed invalid characters | `D_Flair_and_M-I_` |
| Filename truncated | `DÐ` or `D` |
| Temporary download | Original name plus `.part`, `.tmp`, or another temporary suffix |
| Server-generated name | A hash or numeric identifier, possibly without `.rar` |

The most interesting possibility is **a completely different filename**.

There was a pyLoad-ng bug reported in February 2026 where downloads were saved under hash-like names rather than their expected filenames. The issue was closed following a fix to HTTP header parsing. <Cite ref="turn926829search0"/>

This is not proof that you're experiencing the same issue, but it makes searching for files without `OIA90` particularly worthwhile.

## 4. Find the missing file using Python

Rather than guessing filenames, I would search by modification time and file size, and display names using `ascii()`.

This is especially useful because it will reveal unusual Unicode characters without passing them directly to your terminal.

For a large download directory, filter by the approximate download completion time:

Adjust the dates to match your download.

On Linux, you can also search directly:

But the Python approach is safer for filenames containing control characters.

## 5. Check the actual filename bytes on disk

On Linux, filenames are ultimately byte sequences, not necessarily valid UTF-8.

It's possible that pyLoad wrote the corrupted filename literally.

To inspect filenames without decoding them:

This can distinguish between the following cases:

The important distinction is that the same apparent filename can correspond to different byte sequences depending on how it was encoded.

## 6. How to determine whether pyLoad actually wrote the file

I would inspect the download completion sequence rather than relying on the `Download finished` message.

Specifically, log these values immediately before and after the file is opened or renamed:

If pyLoad uses a temporary filename and renames it after downloading, instrument both paths:

This will tell you whether the file was written successfully, whether it was renamed, and which path was used.

One caveat: a `Download finished` log message does not necessarily mean the final filename was already written to disk. That depends on the particular pyLoad version and downloader plugin.

------------------------------------------------------------------------

## 7. My leading suspicion

Given that the log stops at:

I would investigate two separate issues:

**First:** The logging handler may be failing or blocking when processing U+009E. Python's logging implementation has exception handling, but custom handlers and logging-related deadlocks can behave differently. \<Cite refs={\["turn926829search1","turn926829search2"\]}/\>

**Second:** The download may already exist under a temporary or server-generated filename, with the final rename never having completed.

The second possibility is especially plausible if pyLoad logs `Download finished` before performing final file operations.

**One question:** Are you running pyLoad on Linux, inside Docker, or on Windows?

That matters considerably: on Linux, I can give you a byte-exact filesystem search that finds even filenames with invalid UTF-8 sequences, without relying on how the terminal displays them.

## Prompt:

11/19/2026, 12:00:19 PM

here is more of the pyload output

    [2026-11-18 16:27:37]  INFO                pyload  Download starts: DО_Flair_and_MС-IС_-_Rollers_EP-(OIA90)-WEB-FLAC-2025.rar.html
    [2026-11-18 16:27:37]  DEBUG               pyload  addon ExternalScripts: No script found under folder `download_preparing`
    [2026-11-18 16:27:37]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72612]: Plugin version: 0.60
    [2026-11-18 16:27:37]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72612]: Plugin status: testing
    [2026-11-18 16:27:37]  WARNING             pyload  DOWNLOADER RapidgatorNet[72612]: Plugin may be unstable
    [2026-11-18 16:27:37]  INFO                pyload  ACCOUNT RapidgatorNet: Grabbing account info for user `mil****`...
    [2026-11-18 16:27:37]  DEBUG               pyload  ACCOUNT RapidgatorNet: LOAD URL https://rapidgator.net/api/user/info | get={'sid': '7f00e6c89867a20319c8f1cb0f761770'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:27:37]  DEBUG               pyload  ACCOUNT RapidgatorNet: Account info for user `mil****`: {'login': {'password': '**********', 'stats': [42, 1795015652.2524455], 'timestamp': 1795014929.1167738, 'valid': True}, 'data': {'login': 'mil****', 'options': {'limit_dl': ['0']}, 'plugin': <Account RapidgatorNet>, 'premium': True, 'trafficleft': 5014661562753.0, 'type': 'RapidgatorNet', 'validuntil': 1795876083, 'sid': '7f00e6c89867a20319c8f1cb0f761770'}}
    [2026-11-18 16:27:37]  DEBUG               pyload  ACCOUNT RapidgatorNet: Using account mil*******
    [2026-11-18 16:27:37]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72612]: BaseHoster._login: calling self.setup
    [2026-11-18 16:27:37]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72612]: RapidgatorNet.setup: self.premium=True
    [2026-11-18 16:27:37]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: Processing url: https://rapidgator.net/file/e7ecb99248db1c04783d059408e5484f/DО_Flair_and_MС-IС_-_Rollers_EP-(OIA90)-WEB-FLAC-2025.rar.html
    [2026-11-18 16:27:37]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: Looking for direct download link...
    [2026-11-18 16:27:37]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72612]: LOAD URL https://rapidgator.net/file/e7ecb99248db1c04783d059408e5484f | get=None | post=None | referrer=True | cookies=True | just_header=True | decode=True | multipart=False | redirect=False | req=None
    [2026-11-18 16:27:37]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: Direct download link not found
    [2026-11-18 16:27:37]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72612]: LOAD URL https://rapidgator.net/file/e7ecb99248db1c04783d059408e5484f | get=None | post=None | referrer=False | cookies=[('rapidgator.net', 'lang', 'en')] | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:27:37]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: Checking for link errors...
    [2026-11-18 16:27:37]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: No errors found
    [2026-11-18 16:27:37]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: Grabbing link info...
    [2026-11-18 16:27:37]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72612]: Link info: {'name': 'DО_Flair_and_MС-IС_-_Rollers_EP-(OIA90)-WEB-FLAC-2025.rar', 'hash': {}, 'pattern': {'ID': 'e7ecb99248db1c04783d059408e5484f', 'N': 'DО_Flair_and_MС-IС_-_Rollers_EP-(OIA90)-WEB-FLAC-2025.rar', 'S': '143', 'U': 'MB'}, 'size': 149946368, 'status': 2, 'url': 'https://rapidgator.net/file/e7ecb99248db1c04783d059408e5484f'}
    [2026-11-18 16:27:37]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72612]: Previous link info: {}
    [2026-11-18 16:27:37]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: Link name: DО_Flair_and_MС-IС_-_Rollers_EP-(OIA90)-WEB-FLAC-2025.rar
    [2026-11-18 16:27:37]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: Link size: 143.00 MiB (149946368 bytes)
    [2026-11-18 16:27:37]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: Link status: online
    [2026-11-18 16:27:37]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: Processing as premium download...
    [2026-11-18 16:27:37]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72612]: LOAD URL https://rapidgator.net/api/file/info | get={'sid': '7f00e6c89867a20319c8f1cb0f761770', 'url': 'https://rapidgator.net/file/e7ecb99248db1c04783d059408e5484f'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:27:37]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72612]: LOAD URL https://rapidgator.net/api/file/download | get={'sid': '7f00e6c89867a20319c8f1cb0f761770', 'url': 'https://rapidgator.net/file/e7ecb99248db1c04783d059408e5484f'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:27:37]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: Downloading file...
    [2026-11-18 16:27:37]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72612]: DOWNLOAD URL https://s6.rapidgator.net/download/6675d800-1f25-4344-8912-9cf74d30a2e9 | get={} | post={} | referrer=True | cookies=True | disposition=True | resume=None | chunks=None
    [2026-11-18 16:27:37]  DEBUG               pyload  Content-Disposition: 'DÐ\x9e_Flair_and_MÐ¡-IÐ¡_-_Rollers_EP-(OIA90)-WEB-FLAC-2025.rar'
    [2026-11-18 16:27:37]  DEBUG               pyload  Chunk 1 range set to 0-
    [2026-11-18 16:27:41]  DEBUG               pyload  Chunk 1 download finished
    [2026-11-18 16:27:41]  INFO                pyload  DOWNLOADER RapidgatorNet[72613]: File saved
    [2026-11-18 16:27:41]  INFO                pyload  DOWNLOADER RapidgatorNet[72613]: Checking download...
    [2026-11-18 16:27:41]  INFO                pyload  DOWNLOADER RapidgatorNet[72613]: File is OK
    [2026-11-18 16:27:41]  INFO                pyload  DOWNLOADER RapidgatorNet[72613]: Checking file (with built-in rules)...
    [2026-11-18 16:27:41]  INFO                pyload  DOWNLOADER RapidgatorNet[72613]: Checking file (with custom rules)...
    [2026-11-18 16:27:41]  INFO                pyload  DOWNLOADER RapidgatorNet[72613]: Checking for link errors...
    [2026-11-18 16:27:41]  INFO                pyload  DOWNLOADER RapidgatorNet[72613]: No errors found
    [2026-11-18 16:27:41]  DEBUG               pyload  addon ExternalScripts: No script found under folder `download_processed`
    [2026-11-18 16:27:41]  DEBUG               pyload  addon ExternalScripts: No script found under folder `package_processed`
    [2026-11-18 16:27:41]  INFO                pyload  Download finished: Jam_Thieves_-_Bumblebee___Exodus-(KNG019)-WEB-FLAC-2025.rar
    [2026-11-18 16:27:41]  DEBUG               pyload  addon ExternalScripts: No script found under folder `download_finished`
    [2026-11-18 16:27:41]  INFO                pyload  Package finished: Jam Thieves - Bumblebee / Exodus (2025) FLAC
    [2026-11-18 16:27:41]  DEBUG               pyload  addon ExternalScripts: No script found under folder `package_finished`
    [2026-11-18 16:27:41]  DEBUG               pyload  addon ExtractArchive: Use for extensions: .001|.7z|.bz2|.bzip2|.gz|.gzip|.lha|.lzh|.lzma|.rar|.tar|.taz|.tbz|.tbz2|.tgz|.xar|.xz|.z|.zip
    [2026-11-18 16:27:41]  INFO                pyload  addon ExtractArchive: Check package: Jam Thieves - Bumblebee / Exodus (2025) FLAC
    [2026-11-18 16:27:41]  DEBUG               pyload  addon ExtractArchive: Targets for SevenZip: [(72613, '/media/ZYDFB0M9_24TB/Downloads/pyLoad/Jam_Thieves_-_Bumblebee_Exodus_2025_FLAC/Jam_Thieves_-_Bumblebee___Exodus-(KNG019)-WEB-FLAC-2025.rar', '/media/ZYDFB0M9_24TB/Downloads/pyLoad/Jam_Thieves_-_Bumblebee_Exodus_2025_FLAC/')]
    [2026-11-18 16:27:41]  INFO                pyload  addon ExtractArchive: Jam_Thieves_-_Bumblebee___Exodus-(KNG019)-WEB-FLAC-2025.rar | Extract to: /media/ZYDFB0M9_24TB/Downloads/pyLoad/Jam_Thieves_-_Bumblebee_Exodus_2025_FLAC/
    [2026-11-18 16:27:41]  DEBUG               pyload  addon ExtractArchive: Password: None
    [2026-11-18 16:27:41]  DEBUG               pyload  addon ExtractArchive: Verifying using password: None
    [2026-11-18 16:27:41]  DEBUG               pyload  extractor SevenZip: EXECUTE 7z l -scsUTF-8 -sccUTF-8 -bso0 -bsp1 -aos -xr!*.nfo -xr!*.DS_Store -xr!index.dat -xr!thumb.db -p- -slt /media/ZYDFB0M9_24TB/Downloads/pyLoad/Jam_Thieves_-_Bumblebee_Exodus_2025_FLAC/Jam_Thieves_-_Bumblebee___Exodus-(KNG019)-WEB-FLAC-2025.rar
    [2026-11-18 16:27:41]  DEBUG               pyload  addon ExtractArchive: Password Correct
    [2026-11-18 16:27:41]  DEBUG               pyload  addon ExtractArchive: Extracting using password: None
    [2026-11-18 16:27:41]  DEBUG               pyload  extractor SevenZip: EXECUTE 7z l -scsUTF-8 -sccUTF-8 -bso0 -bsp1 -aos -xr!*.nfo -xr!*.DS_Store -xr!index.dat -xr!thumb.db -p- -slt /media/ZYDFB0M9_24TB/Downloads/pyLoad/Jam_Thieves_-_Bumblebee_Exodus_2025_FLAC/Jam_Thieves_-_Bumblebee___Exodus-(KNG019)-WEB-FLAC-2025.rar
    [2026-11-18 16:27:41]  ERROR               pyload  addon ExtractArchive: Jam_Thieves_-_Bumblebee___Exodus-(KNG019)-WEB-FLAC-2025.rar | Archive error | pyload.plugins.base.extractor.ArchiveError: Cannot open file
    Traceback (most recent call last):
      File "/home/user/src/milahu/pyload/src/pyload/plugins/addons/ExtractArchive.py", line 559, in _extract
        archive.extract(password)
        ~~~~~~~~~~~~~~~^^^^^^^^^^
      File "/home/user/src/milahu/pyload/src/pyload/plugins/extractors/SevenZip.py", line 172, in extract
        archive_info = self._get_archive_info(password)
      File "/home/user/src/milahu/pyload/src/pyload/plugins/extractors/SevenZip.py", line 316, in _get_archive_info
        raise ArchiveError(self._("Cannot open file"))
    pyload.plugins.base.extractor.ArchiveError: Cannot open file
    [2026-11-18 16:27:41]  DEBUG               pyload  addon ExternalScripts: No script found under folder `archive_extract_failed`
    [2026-11-18 16:27:41]  ERROR               pyload  addon ExtractArchive: Jam_Thieves_-_Bumblebee___Exodus-(KNG019)-WEB-FLAC-2025.rar | Exception: Extract failed
    Traceback (most recent call last):
      File "/home/user/src/milahu/pyload/src/pyload/plugins/addons/ExtractArchive.py", line 349, in extract
        new_files = self._extract(
            pyfile, archive, pypack.password
        )
      File "/home/user/src/milahu/pyload/src/pyload/plugins/addons/ExtractArchive.py", line 626, in _extract
        raise Exception(self._("Extract failed"))
    Exception: Extract failed
    [2026-11-18 16:27:41]  DEBUG               pyload  addon ExternalScripts: No script found under folder `package_extract_failed`
    [2026-11-18 16:27:41]  DEBUG               pyload  addon ExternalScripts: No script found under folder `archive_processed`
    [2026-11-18 16:27:42]  INFO                pyload  Download starts: Frame_-_Blackjack-(JHRCD024)-WEB-FLAC-2026.rar.html
    [2026-11-18 16:27:42]  DEBUG               pyload  addon ExternalScripts: No script found under folder `download_preparing`
    [2026-11-18 16:27:42]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79270]: Plugin version: 0.60
    [2026-11-18 16:27:42]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79270]: Plugin status: testing
    [2026-11-18 16:27:42]  WARNING             pyload  DOWNLOADER RapidgatorNet[79270]: Plugin may be unstable
    [2026-11-18 16:27:42]  INFO                pyload  ACCOUNT RapidgatorNet: Grabbing account info for user `mil****`...
    [2026-11-18 16:27:42]  DEBUG               pyload  ACCOUNT RapidgatorNet: LOAD URL https://rapidgator.net/api/user/info | get={'sid': '7f00e6c89867a20319c8f1cb0f761770'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:27:42]  DEBUG               pyload  ACCOUNT RapidgatorNet: Account info for user `mil****`: {'login': {'password': '**********', 'stats': [42, 1795015657.2601135], 'timestamp': 1795014929.1167738, 'valid': True}, 'data': {'login': 'mil****', 'options': {'limit_dl': ['0']}, 'plugin': <Account RapidgatorNet>, 'premium': True, 'trafficleft': 5014661562753.0, 'type': 'RapidgatorNet', 'validuntil': 1795876083, 'sid': '7f00e6c89867a20319c8f1cb0f761770'}}
    [2026-11-18 16:27:42]  DEBUG               pyload  ACCOUNT RapidgatorNet: Using account mil*******
    [2026-11-18 16:27:42]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79270]: BaseHoster._login: calling self.setup
    [2026-11-18 16:27:42]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79270]: RapidgatorNet.setup: self.premium=True
    [2026-11-18 16:27:42]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: Processing url: https://rapidgator.net/file/fcb2b8b0c0d694feb635b4d74ca65c11/Frame_-_Blackjack-(JHRCD024)-WEB-FLAC-2026.rar.html
    [2026-11-18 16:27:42]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: Looking for direct download link...
    [2026-11-18 16:27:42]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79270]: LOAD URL https://rapidgator.net/file/fcb2b8b0c0d694feb635b4d74ca65c11 | get=None | post=None | referrer=True | cookies=True | just_header=True | decode=True | multipart=False | redirect=False | req=None
    [2026-11-18 16:27:42]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: Direct download link not found
    [2026-11-18 16:27:42]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79270]: LOAD URL https://rapidgator.net/file/fcb2b8b0c0d694feb635b4d74ca65c11 | get=None | post=None | referrer=False | cookies=[('rapidgator.net', 'lang', 'en')] | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:27:42]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: Checking for link errors...
    [2026-11-18 16:27:42]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: No errors found
    [2026-11-18 16:27:42]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: Grabbing link info...
    [2026-11-18 16:27:42]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79270]: Link info: {'name': 'Frame_-_Blackjack-(JHRCD024)-WEB-FLAC-2026.rar', 'hash': {}, 'pattern': {'ID': 'fcb2b8b0c0d694feb635b4d74ca65c11', 'N': 'Frame_-_Blackjack-(JHRCD024)-WEB-FLAC-2026.rar', 'S': '35.19', 'U': 'MB'}, 'size': 36899389, 'status': 2, 'url': 'https://rapidgator.net/file/fcb2b8b0c0d694feb635b4d74ca65c11'}
    [2026-11-18 16:27:42]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79270]: Previous link info: {}
    [2026-11-18 16:27:42]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: Link name: Frame_-_Blackjack-(JHRCD024)-WEB-FLAC-2026.rar
    [2026-11-18 16:27:42]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: Link size: 35.19 MiB (36899389 bytes)
    [2026-11-18 16:27:42]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: Link status: online
    [2026-11-18 16:27:42]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: Processing as premium download...
    [2026-11-18 16:27:42]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79270]: LOAD URL https://rapidgator.net/api/file/info | get={'sid': '7f00e6c89867a20319c8f1cb0f761770', 'url': 'https://rapidgator.net/file/fcb2b8b0c0d694feb635b4d74ca65c11'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:27:42]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79270]: LOAD URL https://rapidgator.net/api/file/download | get={'sid': '7f00e6c89867a20319c8f1cb0f761770', 'url': 'https://rapidgator.net/file/fcb2b8b0c0d694feb635b4d74ca65c11'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:27:42]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: Downloading file...
    [2026-11-18 16:27:42]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79270]: DOWNLOAD URL https://s88.rapidgator.net/download/f14287b7-4c90-4b8d-b7c6-c102798b0054 | get={} | post={} | referrer=True | cookies=True | disposition=True | resume=None | chunks=None
    [2026-11-18 16:27:43]  DEBUG               pyload  Content-Disposition: 'Frame_-_Blackjack-(JHRCD024)-WEB-FLAC-2026.rar'
    [2026-11-18 16:27:43]  DEBUG               pyload  Chunk 1 range set to 0-
    [2026-11-18 16:27:55]  DEBUG               pyload  Chunk 1 download finished
    [2026-11-18 16:27:55]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: File saved
    [2026-11-18 16:27:55]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: Checking download...
    [2026-11-18 16:27:55]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: File is OK
    [2026-11-18 16:27:55]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: Checking file (with built-in rules)...
    [2026-11-18 16:27:55]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: Checking file (with custom rules)...
    [2026-11-18 16:27:55]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: Checking for link errors...
    [2026-11-18 16:27:55]  INFO                pyload  DOWNLOADER RapidgatorNet[79270]: No errors found
    [2026-11-18 16:27:55]  DEBUG               pyload  addon ExternalScripts: No script found under folder `download_processed`
    [2026-11-18 16:27:55]  DEBUG               pyload  addon ExternalScripts: No script found under folder `package_processed`
    [2026-11-18 16:27:55]  INFO                pyload  Download finished: Frame_-_Blackjack-(JHRCD024)-WEB-FLAC-2026.rar
    [2026-11-18 16:27:55]  DEBUG               pyload  addon ExternalScripts: No script found under folder `download_finished`
    [2026-11-18 16:27:55]  INFO                pyload  Package finished: Frame - Blackjack (2026) FLAC
    [2026-11-18 16:27:55]  DEBUG               pyload  addon ExternalScripts: No script found under folder `package_finished`
    [2026-11-18 16:27:55]  DEBUG               pyload  addon ExtractArchive: Use for extensions: .001|.7z|.bz2|.bzip2|.gz|.gzip|.lha|.lzh|.lzma|.rar|.tar|.taz|.tbz|.tbz2|.tgz|.xar|.xz|.z|.zip
    [2026-11-18 16:27:55]  INFO                pyload  addon ExtractArchive: Check package: Frame - Blackjack (2026) FLAC
    [2026-11-18 16:27:56]  DEBUG               pyload  addon ExtractArchive: Targets for SevenZip: [(79270, '/media/ZYDFB0M9_24TB/Downloads/pyLoad/Frame_-_Blackjack_2026_FLAC/Frame_-_Blackjack-(JHRCD024)-WEB-FLAC-2026.rar', '/media/ZYDFB0M9_24TB/Downloads/pyLoad/Frame_-_Blackjack_2026_FLAC/')]
    [2026-11-18 16:27:56]  INFO                pyload  addon ExtractArchive: Frame_-_Blackjack-(JHRCD024)-WEB-FLAC-2026.rar | Extract to: /media/ZYDFB0M9_24TB/Downloads/pyLoad/Frame_-_Blackjack_2026_FLAC/
    [2026-11-18 16:27:56]  DEBUG               pyload  addon ExtractArchive: Password: None
    [2026-11-18 16:27:56]  DEBUG               pyload  addon ExtractArchive: Verifying using password: None
    [2026-11-18 16:27:56]  DEBUG               pyload  extractor SevenZip: EXECUTE 7z l -scsUTF-8 -sccUTF-8 -bso0 -bsp1 -aos -xr!*.nfo -xr!*.DS_Store -xr!index.dat -xr!thumb.db -p- -slt /media/ZYDFB0M9_24TB/Downloads/pyLoad/Frame_-_Blackjack_2026_FLAC/Frame_-_Blackjack-(JHRCD024)-WEB-FLAC-2026.rar
    [2026-11-18 16:27:56]  DEBUG               pyload  addon ExtractArchive: Password Correct
    [2026-11-18 16:27:56]  DEBUG               pyload  addon ExtractArchive: Extracting using password: None
    [2026-11-18 16:27:56]  DEBUG               pyload  extractor SevenZip: EXECUTE 7z l -scsUTF-8 -sccUTF-8 -bso0 -bsp1 -aos -xr!*.nfo -xr!*.DS_Store -xr!index.dat -xr!thumb.db -p- -slt /media/ZYDFB0M9_24TB/Downloads/pyLoad/Frame_-_Blackjack_2026_FLAC/Frame_-_Blackjack-(JHRCD024)-WEB-FLAC-2026.rar
    [2026-11-18 16:27:56]  ERROR               pyload  addon ExtractArchive: Frame_-_Blackjack-(JHRCD024)-WEB-FLAC-2026.rar | Archive error | pyload.plugins.base.extractor.ArchiveError: Cannot open file
    Traceback (most recent call last):
      File "/home/user/src/milahu/pyload/src/pyload/plugins/addons/ExtractArchive.py", line 559, in _extract
        archive.extract(password)
        ~~~~~~~~~~~~~~~^^^^^^^^^^
      File "/home/user/src/milahu/pyload/src/pyload/plugins/extractors/SevenZip.py", line 172, in extract
        archive_info = self._get_archive_info(password)
      File "/home/user/src/milahu/pyload/src/pyload/plugins/extractors/SevenZip.py", line 316, in _get_archive_info
        raise ArchiveError(self._("Cannot open file"))
    pyload.plugins.base.extractor.ArchiveError: Cannot open file
    [2026-11-18 16:27:56]  DEBUG               pyload  addon ExternalScripts: No script found under folder `archive_extract_failed`
    [2026-11-18 16:27:56]  ERROR               pyload  addon ExtractArchive: Frame_-_Blackjack-(JHRCD024)-WEB-FLAC-2026.rar | Exception: Extract failed
    Traceback (most recent call last):
      File "/home/user/src/milahu/pyload/src/pyload/plugins/addons/ExtractArchive.py", line 349, in extract
        new_files = self._extract(
            pyfile, archive, pypack.password
        )
      File "/home/user/src/milahu/pyload/src/pyload/plugins/addons/ExtractArchive.py", line 626, in _extract
        raise Exception(self._("Extract failed"))
    Exception: Extract failed
    [2026-11-18 16:27:56]  DEBUG               pyload  addon ExternalScripts: No script found under folder `package_extract_failed`
    [2026-11-18 16:27:56]  DEBUG               pyload  addon ExternalScripts: No script found under folder `archive_processed`
    [2026-11-18 16:27:56]  INFO                pyload  Download starts: Aydn_-_Gaijin-(UKF169)-WEB-FLAC-2025.rar.html
    [2026-11-18 16:27:56]  DEBUG               pyload  addon ExternalScripts: No script found under folder `download_preparing`
    [2026-11-18 16:27:56]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72611]: Plugin version: 0.60
    [2026-11-18 16:27:56]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72611]: Plugin status: testing
    [2026-11-18 16:27:56]  WARNING             pyload  DOWNLOADER RapidgatorNet[72611]: Plugin may be unstable
    [2026-11-18 16:27:56]  INFO                pyload  ACCOUNT RapidgatorNet: Grabbing account info for user `mil****`...
    [2026-11-18 16:27:56]  DEBUG               pyload  ACCOUNT RapidgatorNet: LOAD URL https://rapidgator.net/api/user/info | get={'sid': '7f00e6c89867a20319c8f1cb0f761770'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:27:56]  DEBUG               pyload  ACCOUNT RapidgatorNet: Account info for user `mil****`: {'login': {'password': '**********', 'stats': [42, 1795015662.2893078], 'timestamp': 1795014929.1167738, 'valid': True}, 'data': {'login': 'mil****', 'options': {'limit_dl': ['0']}, 'plugin': <Account RapidgatorNet>, 'premium': True, 'trafficleft': 5014590137903.0, 'type': 'RapidgatorNet', 'validuntil': 1795876083, 'sid': '7f00e6c89867a20319c8f1cb0f761770'}}
    [2026-11-18 16:27:56]  DEBUG               pyload  ACCOUNT RapidgatorNet: Using account mil*******
    [2026-11-18 16:27:56]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72611]: BaseHoster._login: calling self.setup
    [2026-11-18 16:27:56]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72611]: RapidgatorNet.setup: self.premium=True
    [2026-11-18 16:27:56]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: Processing url: https://rapidgator.net/file/f280080a62e1940cf245b2d4fde4ac8f/Aydn_-_Gaijin-(UKF169)-WEB-FLAC-2025.rar.html
    [2026-11-18 16:27:56]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: Looking for direct download link...
    [2026-11-18 16:27:56]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72611]: LOAD URL https://rapidgator.net/file/f280080a62e1940cf245b2d4fde4ac8f | get=None | post=None | referrer=True | cookies=True | just_header=True | decode=True | multipart=False | redirect=False | req=None
    [2026-11-18 16:27:56]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: Direct download link not found
    [2026-11-18 16:27:56]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72611]: LOAD URL https://rapidgator.net/file/f280080a62e1940cf245b2d4fde4ac8f | get=None | post=None | referrer=False | cookies=[('rapidgator.net', 'lang', 'en')] | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:27:56]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: Checking for link errors...
    [2026-11-18 16:27:56]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: No errors found
    [2026-11-18 16:27:56]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: Grabbing link info...
    [2026-11-18 16:27:56]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72611]: Link info: {'name': 'Aydn_-_Gaijin-(UKF169)-WEB-FLAC-2025.rar', 'hash': {}, 'pattern': {'ID': 'f280080a62e1940cf245b2d4fde4ac8f', 'N': 'Aydn_-_Gaijin-(UKF169)-WEB-FLAC-2025.rar', 'S': '25.51', 'U': 'MB'}, 'size': 26749173, 'status': 2, 'url': 'https://rapidgator.net/file/f280080a62e1940cf245b2d4fde4ac8f'}
    [2026-11-18 16:27:56]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72611]: Previous link info: {}
    [2026-11-18 16:27:56]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: Link name: Aydn_-_Gaijin-(UKF169)-WEB-FLAC-2025.rar
    [2026-11-18 16:27:56]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: Link size: 25.51 MiB (26749173 bytes)
    [2026-11-18 16:27:56]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: Link status: online
    [2026-11-18 16:27:56]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: Processing as premium download...
    [2026-11-18 16:27:56]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72611]: LOAD URL https://rapidgator.net/api/file/info | get={'sid': '7f00e6c89867a20319c8f1cb0f761770', 'url': 'https://rapidgator.net/file/f280080a62e1940cf245b2d4fde4ac8f'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:27:56]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72611]: LOAD URL https://rapidgator.net/api/file/download | get={'sid': '7f00e6c89867a20319c8f1cb0f761770', 'url': 'https://rapidgator.net/file/f280080a62e1940cf245b2d4fde4ac8f'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:27:56]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: Downloading file...
    [2026-11-18 16:27:56]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72611]: DOWNLOAD URL https://s12.rapidgator.net/download/9bbadaa4-da7a-4a28-878c-1a882a21db9d | get={} | post={} | referrer=True | cookies=True | disposition=True | resume=None | chunks=None
    [2026-11-18 16:27:57]  DEBUG               pyload  Content-Disposition: 'Aydn_-_Gaijin-(UKF169)-WEB-FLAC-2025.rar'
    [2026-11-18 16:27:57]  DEBUG               pyload  Chunk 1 range set to 0-
    [2026-11-18 16:28:04]  DEBUG               pyload  Chunk 1 download finished
    [2026-11-18 16:28:04]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: File saved
    [2026-11-18 16:28:04]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: Checking download...
    [2026-11-18 16:28:04]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: File is OK
    [2026-11-18 16:28:04]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: Checking file (with built-in rules)...
    [2026-11-18 16:28:04]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: Checking file (with custom rules)...
    [2026-11-18 16:28:04]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: Checking for link errors...
    [2026-11-18 16:28:04]  INFO                pyload  DOWNLOADER RapidgatorNet[72611]: No errors found
    [2026-11-18 16:28:04]  DEBUG               pyload  addon ExternalScripts: No script found under folder `download_processed`
    [2026-11-18 16:28:04]  DEBUG               pyload  addon ExternalScripts: No script found under folder `package_processed`
    [2026-11-18 16:28:04]  INFO                pyload  Download finished: Aydn_-_Gaijin-(UKF169)-WEB-FLAC-2025.rar
    [2026-11-18 16:28:04]  DEBUG               pyload  addon ExternalScripts: No script found under folder `download_finished`
    [2026-11-18 16:28:04]  INFO                pyload  Package finished: Aydn - Gaijin (2025) FLAC
    [2026-11-18 16:28:04]  DEBUG               pyload  addon ExternalScripts: No script found under folder `package_finished`
    [2026-11-18 16:28:04]  DEBUG               pyload  addon ExtractArchive: Use for extensions: .001|.7z|.bz2|.bzip2|.gz|.gzip|.lha|.lzh|.lzma|.rar|.tar|.taz|.tbz|.tbz2|.tgz|.xar|.xz|.z|.zip
    [2026-11-18 16:28:04]  INFO                pyload  addon ExtractArchive: Check package: Aydn - Gaijin (2025) FLAC
    [2026-11-18 16:28:04]  DEBUG               pyload  addon ExtractArchive: Targets for SevenZip: [(72611, '/media/ZYDFB0M9_24TB/Downloads/pyLoad/Aydn_-_Gaijin_2025_FLAC/Aydn_-_Gaijin-(UKF169)-WEB-FLAC-2025.rar', '/media/ZYDFB0M9_24TB/Downloads/pyLoad/Aydn_-_Gaijin_2025_FLAC/')]
    [2026-11-18 16:28:04]  INFO                pyload  addon ExtractArchive: Aydn_-_Gaijin-(UKF169)-WEB-FLAC-2025.rar | Extract to: /media/ZYDFB0M9_24TB/Downloads/pyLoad/Aydn_-_Gaijin_2025_FLAC/
    [2026-11-18 16:28:04]  DEBUG               pyload  addon ExtractArchive: Password: None
    [2026-11-18 16:28:04]  DEBUG               pyload  addon ExtractArchive: Verifying using password: None
    [2026-11-18 16:28:04]  DEBUG               pyload  extractor SevenZip: EXECUTE 7z l -scsUTF-8 -sccUTF-8 -bso0 -bsp1 -aos -xr!*.nfo -xr!*.DS_Store -xr!index.dat -xr!thumb.db -p- -slt /media/ZYDFB0M9_24TB/Downloads/pyLoad/Aydn_-_Gaijin_2025_FLAC/Aydn_-_Gaijin-(UKF169)-WEB-FLAC-2025.rar
    [2026-11-18 16:28:04]  DEBUG               pyload  addon ExtractArchive: Password Correct
    [2026-11-18 16:28:04]  DEBUG               pyload  addon ExtractArchive: Extracting using password: None
    [2026-11-18 16:28:04]  DEBUG               pyload  extractor SevenZip: EXECUTE 7z l -scsUTF-8 -sccUTF-8 -bso0 -bsp1 -aos -xr!*.nfo -xr!*.DS_Store -xr!index.dat -xr!thumb.db -p- -slt /media/ZYDFB0M9_24TB/Downloads/pyLoad/Aydn_-_Gaijin_2025_FLAC/Aydn_-_Gaijin-(UKF169)-WEB-FLAC-2025.rar
    [2026-11-18 16:28:04]  ERROR               pyload  addon ExtractArchive: Aydn_-_Gaijin-(UKF169)-WEB-FLAC-2025.rar | Archive error | pyload.plugins.base.extractor.ArchiveError: Cannot open file
    Traceback (most recent call last):
      File "/home/user/src/milahu/pyload/src/pyload/plugins/addons/ExtractArchive.py", line 559, in _extract
        archive.extract(password)
        ~~~~~~~~~~~~~~~^^^^^^^^^^
      File "/home/user/src/milahu/pyload/src/pyload/plugins/extractors/SevenZip.py", line 172, in extract
        archive_info = self._get_archive_info(password)
      File "/home/user/src/milahu/pyload/src/pyload/plugins/extractors/SevenZip.py", line 316, in _get_archive_info
        raise ArchiveError(self._("Cannot open file"))
    pyload.plugins.base.extractor.ArchiveError: Cannot open file
    [2026-11-18 16:28:04]  DEBUG               pyload  addon ExternalScripts: No script found under folder `archive_extract_failed`
    [2026-11-18 16:28:04]  ERROR               pyload  addon ExtractArchive: Aydn_-_Gaijin-(UKF169)-WEB-FLAC-2025.rar | Exception: Extract failed
    Traceback (most recent call last):
      File "/home/user/src/milahu/pyload/src/pyload/plugins/addons/ExtractArchive.py", line 349, in extract
        new_files = self._extract(
            pyfile, archive, pypack.password
        )
      File "/home/user/src/milahu/pyload/src/pyload/plugins/addons/ExtractArchive.py", line 626, in _extract
        raise Exception(self._("Extract failed"))
    Exception: Extract failed
    [2026-11-18 16:28:04]  DEBUG               pyload  addon ExternalScripts: No script found under folder `package_extract_failed`
    [2026-11-18 16:28:04]  DEBUG               pyload  addon ExternalScripts: No script found under folder `archive_processed`
    [2026-11-18 16:28:05]  INFO                pyload  Download starts: Joy_Mobility_-_Now_We_Are_Strangers___Do_It-(AOR276)-WEB-FLAC-2026.rar.html
    [2026-11-18 16:28:05]  DEBUG               pyload  addon ExternalScripts: No script found under folder `download_preparing`
    [2026-11-18 16:28:05]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79271]: Plugin version: 0.60
    [2026-11-18 16:28:05]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79271]: Plugin status: testing
    [2026-11-18 16:28:05]  WARNING             pyload  DOWNLOADER RapidgatorNet[79271]: Plugin may be unstable
    [2026-11-18 16:28:05]  INFO                pyload  ACCOUNT RapidgatorNet: Grabbing account info for user `mil****`...
    [2026-11-18 16:28:05]  DEBUG               pyload  ACCOUNT RapidgatorNet: LOAD URL https://rapidgator.net/api/user/info | get={'sid': '7f00e6c89867a20319c8f1cb0f761770'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:28:05]  DEBUG               pyload  ACCOUNT RapidgatorNet: Account info for user `mil****`: {'login': {'password': '**********', 'stats': [42, 1795015676.3042216], 'timestamp': 1795014929.1167738, 'valid': True}, 'data': {'login': 'mil****', 'options': {'limit_dl': ['0']}, 'plugin': <Account RapidgatorNet>, 'premium': True, 'trafficleft': 5014526488152.0, 'type': 'RapidgatorNet', 'validuntil': 1795876083, 'sid': '7f00e6c89867a20319c8f1cb0f761770'}}
    [2026-11-18 16:28:05]  DEBUG               pyload  ACCOUNT RapidgatorNet: Using account mil*******
    [2026-11-18 16:28:05]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79271]: BaseHoster._login: calling self.setup
    [2026-11-18 16:28:05]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79271]: RapidgatorNet.setup: self.premium=True
    [2026-11-18 16:28:05]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: Processing url: https://rapidgator.net/file/18d975a6f6138e6fbb275714be390009/Joy_Mobility_-_Now_We_Are_Strangers___Do_It-(AOR276)-WEB-FLAC-2026.rar.html
    [2026-11-18 16:28:05]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: Looking for direct download link...
    [2026-11-18 16:28:05]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79271]: LOAD URL https://rapidgator.net/file/18d975a6f6138e6fbb275714be390009 | get=None | post=None | referrer=True | cookies=True | just_header=True | decode=True | multipart=False | redirect=False | req=None
    [2026-11-18 16:28:05]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: Direct download link not found
    [2026-11-18 16:28:05]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79271]: LOAD URL https://rapidgator.net/file/18d975a6f6138e6fbb275714be390009 | get=None | post=None | referrer=False | cookies=[('rapidgator.net', 'lang', 'en')] | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:28:05]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: Checking for link errors...
    [2026-11-18 16:28:05]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: No errors found
    [2026-11-18 16:28:05]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: Grabbing link info...
    [2026-11-18 16:28:05]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79271]: Link info: {'name': 'Joy_Mobility_-_Now_We_Are_Strangers___Do_It-(AOR276)-WEB-FLAC-2026.rar', 'hash': {}, 'pattern': {'ID': '18d975a6f6138e6fbb275714be390009', 'N': 'Joy_Mobility_-_Now_We_Are_Strangers___Do_It-(AOR276)-WEB-FLAC-2026.rar', 'S': '73.25', 'U': 'MB'}, 'size': 76808192, 'status': 2, 'url': 'https://rapidgator.net/file/18d975a6f6138e6fbb275714be390009'}
    [2026-11-18 16:28:05]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79271]: Previous link info: {}
    [2026-11-18 16:28:05]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: Link name: Joy_Mobility_-_Now_We_Are_Strangers___Do_It-(AOR276)-WEB-FLAC-2026.rar
    [2026-11-18 16:28:05]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: Link size: 73.25 MiB (76808192 bytes)
    [2026-11-18 16:28:05]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: Link status: online
    [2026-11-18 16:28:05]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: Processing as premium download...
    [2026-11-18 16:28:05]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79271]: LOAD URL https://rapidgator.net/api/file/info | get={'sid': '7f00e6c89867a20319c8f1cb0f761770', 'url': 'https://rapidgator.net/file/18d975a6f6138e6fbb275714be390009'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:28:05]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79271]: LOAD URL https://rapidgator.net/api/file/download | get={'sid': '7f00e6c89867a20319c8f1cb0f761770', 'url': 'https://rapidgator.net/file/18d975a6f6138e6fbb275714be390009'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:28:05]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: Downloading file...
    [2026-11-18 16:28:05]  DEBUG               pyload  DOWNLOADER RapidgatorNet[79271]: DOWNLOAD URL https://s48.rapidgator.net/download/7b417c71-228e-4c96-ad7a-54b569aa5345 | get={} | post={} | referrer=True | cookies=True | disposition=True | resume=None | chunks=None
    [2026-11-18 16:28:06]  DEBUG               pyload  Content-Disposition: 'Joy_Mobility_-_Now_We_Are_Strangers___Do_It-(AOR276)-WEB-FLAC-2026.rar'
    [2026-11-18 16:28:06]  DEBUG               pyload  Chunk 1 range set to 0-
    [2026-11-18 16:28:32]  DEBUG               pyload  Chunk 1 download finished
    [2026-11-18 16:28:32]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: File saved
    [2026-11-18 16:28:32]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: Checking download...
    [2026-11-18 16:28:32]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: File is OK
    [2026-11-18 16:28:32]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: Checking file (with built-in rules)...
    [2026-11-18 16:28:32]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: Checking file (with custom rules)...
    [2026-11-18 16:28:32]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: Checking for link errors...
    [2026-11-18 16:28:32]  INFO                pyload  DOWNLOADER RapidgatorNet[79271]: No errors found
    [2026-11-18 16:28:32]  DEBUG               pyload  addon ExternalScripts: No script found under folder `download_processed`
    [2026-11-18 16:28:32]  DEBUG               pyload  addon ExternalScripts: No script found under folder `package_processed`
    [2026-11-18 16:28:32]  INFO                pyload  Download finished: Joy_Mobility_-_Now_We_Are_Strangers___Do_It-(AOR276)-WEB-FLAC-2026.rar
    [2026-11-18 16:28:32]  DEBUG               pyload  addon ExternalScripts: No script found under folder `download_finished`
    [2026-11-18 16:28:32]  INFO                pyload  Package finished: Joy Mobility - Now We Are Strangers / Do It (2026) FLAC
    [2026-11-18 16:28:32]  DEBUG               pyload  addon ExternalScripts: No script found under folder `package_finished`
    [2026-11-18 16:28:32]  DEBUG               pyload  addon ExtractArchive: Use for extensions: .001|.7z|.bz2|.bzip2|.gz|.gzip|.lha|.lzh|.lzma|.rar|.tar|.taz|.tbz|.tbz2|.tgz|.xar|.xz|.z|.zip
    [2026-11-18 16:28:32]  INFO                pyload  addon ExtractArchive: Check package: Joy Mobility - Now We Are Strangers / Do It (2026) FLAC
    [2026-11-18 16:28:32]  DEBUG               pyload  addon ExtractArchive: Targets for SevenZip: [(79271, '/media/ZYDFB0M9_24TB/Downloads/pyLoad/Joy_Mobility_-_Now_We_Are_Strangers_Do_It_2026_FLAC/Joy_Mobility_-_Now_We_Are_Strangers___Do_It-(AOR276)-WEB-FLAC-2026.rar', '/media/ZYDFB0M9_24TB/Downloads/pyLoad/Joy_Mobility_-_Now_We_Are_Strangers_Do_It_2026_FLAC/')]
    [2026-11-18 16:28:32]  INFO                pyload  addon ExtractArchive: Joy_Mobility_-_Now_We_Are_Strangers___Do_It-(AOR276)-WEB-FLAC-2026.rar | Extract to: /media/ZYDFB0M9_24TB/Downloads/pyLoad/Joy_Mobility_-_Now_We_Are_Strangers_Do_It_2026_FLAC/
    [2026-11-18 16:28:32]  DEBUG               pyload  addon ExtractArchive: Password: None
    [2026-11-18 16:28:32]  DEBUG               pyload  addon ExtractArchive: Verifying using password: None
    [2026-11-18 16:28:32]  DEBUG               pyload  extractor SevenZip: EXECUTE 7z l -scsUTF-8 -sccUTF-8 -bso0 -bsp1 -aos -xr!*.nfo -xr!*.DS_Store -xr!index.dat -xr!thumb.db -p- -slt /media/ZYDFB0M9_24TB/Downloads/pyLoad/Joy_Mobility_-_Now_We_Are_Strangers_Do_It_2026_FLAC/Joy_Mobility_-_Now_We_Are_Strangers___Do_It-(AOR276)-WEB-FLAC-2026.rar
    [2026-11-18 16:28:33]  DEBUG               pyload  addon ExtractArchive: Password Correct
    [2026-11-18 16:28:33]  DEBUG               pyload  addon ExtractArchive: Extracting using password: None
    [2026-11-18 16:28:33]  DEBUG               pyload  extractor SevenZip: EXECUTE 7z l -scsUTF-8 -sccUTF-8 -bso0 -bsp1 -aos -xr!*.nfo -xr!*.DS_Store -xr!index.dat -xr!thumb.db -p- -slt /media/ZYDFB0M9_24TB/Downloads/pyLoad/Joy_Mobility_-_Now_We_Are_Strangers_Do_It_2026_FLAC/Joy_Mobility_-_Now_We_Are_Strangers___Do_It-(AOR276)-WEB-FLAC-2026.rar
    [2026-11-18 16:28:33]  ERROR               pyload  addon ExtractArchive: Joy_Mobility_-_Now_We_Are_Strangers___Do_It-(AOR276)-WEB-FLAC-2026.rar | Archive error | pyload.plugins.base.extractor.ArchiveError: Cannot open file
    Traceback (most recent call last):
      File "/home/user/src/milahu/pyload/src/pyload/plugins/addons/ExtractArchive.py", line 559, in _extract
        archive.extract(password)
        ~~~~~~~~~~~~~~~^^^^^^^^^^
      File "/home/user/src/milahu/pyload/src/pyload/plugins/extractors/SevenZip.py", line 172, in extract
        archive_info = self._get_archive_info(password)
      File "/home/user/src/milahu/pyload/src/pyload/plugins/extractors/SevenZip.py", line 316, in _get_archive_info
        raise ArchiveError(self._("Cannot open file"))
    pyload.plugins.base.extractor.ArchiveError: Cannot open file
    [2026-11-18 16:28:33]  DEBUG               pyload  addon ExternalScripts: No script found under folder `archive_extract_failed`
    [2026-11-18 16:28:33]  ERROR               pyload  addon ExtractArchive: Joy_Mobility_-_Now_We_Are_Strangers___Do_It-(AOR276)-WEB-FLAC-2026.rar | Exception: Extract failed
    Traceback (most recent call last):
      File "/home/user/src/milahu/pyload/src/pyload/plugins/addons/ExtractArchive.py", line 349, in extract
        new_files = self._extract(
            pyfile, archive, pypack.password
        )
      File "/home/user/src/milahu/pyload/src/pyload/plugins/addons/ExtractArchive.py", line 626, in _extract
        raise Exception(self._("Extract failed"))
    Exception: Extract failed
    [2026-11-18 16:28:33]  DEBUG               pyload  addon ExternalScripts: No script found under folder `package_extract_failed`
    [2026-11-18 16:28:33]  DEBUG               pyload  addon ExternalScripts: No script found under folder `archive_processed`
    [2026-11-18 16:28:33]  INFO                pyload  Download starts: VA_-_Annual_2024-WEB-FLAC-2025.part1.rar.html
    [2026-11-18 16:28:33]  DEBUG               pyload  addon ExternalScripts: No script found under folder `download_preparing`
    [2026-11-18 16:28:33]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72609]: Plugin version: 0.60
    [2026-11-18 16:28:33]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72609]: Plugin status: testing
    [2026-11-18 16:28:33]  WARNING             pyload  DOWNLOADER RapidgatorNet[72609]: Plugin may be unstable
    [2026-11-18 16:28:33]  INFO                pyload  ACCOUNT RapidgatorNet: Grabbing account info for user `mil****`...
    [2026-11-18 16:28:33]  DEBUG               pyload  ACCOUNT RapidgatorNet: LOAD URL https://rapidgator.net/api/user/info | get={'sid': '7f00e6c89867a20319c8f1cb0f761770'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:28:33]  DEBUG               pyload  ACCOUNT RapidgatorNet: Account info for user `mil****`: {'login': {'password': '**********', 'stats': [42, 1795015685.479085], 'timestamp': 1795014929.1167738, 'valid': True}, 'data': {'login': 'mil****', 'options': {'limit_dl': ['0']}, 'plugin': <Account RapidgatorNet>, 'premium': True, 'trafficleft': 5014449682408.0, 'type': 'RapidgatorNet', 'validuntil': 1795876083, 'sid': '7f00e6c89867a20319c8f1cb0f761770'}}
    [2026-11-18 16:28:33]  DEBUG               pyload  ACCOUNT RapidgatorNet: Using account mil*******
    [2026-11-18 16:28:33]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72609]: BaseHoster._login: calling self.setup
    [2026-11-18 16:28:33]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72609]: RapidgatorNet.setup: self.premium=True
    [2026-11-18 16:28:33]  INFO                pyload  DOWNLOADER RapidgatorNet[72609]: Processing url: https://rapidgator.net/file/e7e82baa85c0fddd161462598a4b1906/VA_-_Annual_2024-WEB-FLAC-2025.part1.rar.html
    [2026-11-18 16:28:33]  INFO                pyload  DOWNLOADER RapidgatorNet[72609]: Looking for direct download link...
    [2026-11-18 16:28:33]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72609]: LOAD URL https://rapidgator.net/file/e7e82baa85c0fddd161462598a4b1906 | get=None | post=None | referrer=True | cookies=True | just_header=True | decode=True | multipart=False | redirect=False | req=None
    [2026-11-18 16:28:33]  INFO                pyload  DOWNLOADER RapidgatorNet[72609]: Direct download link not found
    [2026-11-18 16:28:33]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72609]: LOAD URL https://rapidgator.net/file/e7e82baa85c0fddd161462598a4b1906 | get=None | post=None | referrer=False | cookies=[('rapidgator.net', 'lang', 'en')] | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:28:33]  INFO                pyload  DOWNLOADER RapidgatorNet[72609]: Checking for link errors...
    [2026-11-18 16:28:33]  INFO                pyload  DOWNLOADER RapidgatorNet[72609]: No errors found
    [2026-11-18 16:28:33]  INFO                pyload  DOWNLOADER RapidgatorNet[72609]: Grabbing link info...
    [2026-11-18 16:28:33]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72609]: Link info: {'name': 'VA_-_Annual_2024-WEB-FLAC-2025.part1.rar', 'hash': {}, 'pattern': {'ID': 'e7e82baa85c0fddd161462598a4b1906', 'N': 'VA_-_Annual_2024-WEB-FLAC-2025.part1.rar', 'S': '900', 'U': 'MB'}, 'size': 943718400, 'status': 2, 'url': 'https://rapidgator.net/file/e7e82baa85c0fddd161462598a4b1906'}
    [2026-11-18 16:28:33]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72609]: Previous link info: {}
    [2026-11-18 16:28:33]  INFO                pyload  DOWNLOADER RapidgatorNet[72609]: Link name: VA_-_Annual_2024-WEB-FLAC-2025.part1.rar
    [2026-11-18 16:28:33]  INFO                pyload  DOWNLOADER RapidgatorNet[72609]: Link size: 900.00 MiB (943718400 bytes)
    [2026-11-18 16:28:33]  INFO                pyload  DOWNLOADER RapidgatorNet[72609]: Link status: online
    [2026-11-18 16:28:33]  INFO                pyload  DOWNLOADER RapidgatorNet[72609]: Processing as premium download...
    [2026-11-18 16:28:33]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72609]: LOAD URL https://rapidgator.net/api/file/info | get={'sid': '7f00e6c89867a20319c8f1cb0f761770', 'url': 'https://rapidgator.net/file/e7e82baa85c0fddd161462598a4b1906'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:28:33]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72609]: LOAD URL https://rapidgator.net/api/file/download | get={'sid': '7f00e6c89867a20319c8f1cb0f761770', 'url': 'https://rapidgator.net/file/e7e82baa85c0fddd161462598a4b1906'} | post=None | referrer=True | cookies=True | just_header=False | decode=True | multipart=False | redirect=True | req=None
    [2026-11-18 16:28:33]  INFO                pyload  DOWNLOADER RapidgatorNet[72609]: Downloading file...
    [2026-11-18 16:28:33]  DEBUG               pyload  DOWNLOADER RapidgatorNet[72609]: DOWNLOAD URL https://s88.rapidgator.net/download/4796c986-0a8a-4c8e-af1a-03c0f25f22ea | get={} | post={} | referrer=True | cookies=True | disposition=True | resume=None | chunks=None
    [2026-11-18 16:28:34]  DEBUG               pyload  Content-Disposition: 'VA_-_Annual_2024-WEB-FLAC-2025.part1.rar'
    [2026-11-18 16:28:34]  DEBUG               pyload  Chunk 1 range set to 0-
    [2026-11-18 16:28:48]  DEBUG               pyload  Chunk 1 download finished
    [2026-11-18 16:28:48]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: File saved
    [2026-11-18 16:28:48]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: Checking download...
    [2026-11-18 16:28:48]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: File is OK
    [2026-11-18 16:28:48]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: Checking file (with built-in rules)...
    [2026-11-18 16:28:48]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: Checking file (with custom rules)...
    [2026-11-18 16:28:48]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: Checking for link errors...
    [2026-11-18 16:28:48]  INFO                pyload  DOWNLOADER RapidgatorNet[72612]: No errors found
    [2026-11-18 16:28:48]  DEBUG               pyload  addon ExternalScripts: No script found under folder `download_processed`
    [2026-11-18 16:28:48]  DEBUG               pyload  addon ExternalScripts: No script found under folder `package_processed`
    [2026-11-18 16:28:48]  INFO                pyload  Download finished: DÐ

note:

    [2026-11-18 16:27:37]  DEBUG               pyload  Content-Disposition: 'DÐ\x9e_Flair_and_MÐ¡-IÐ¡_-_Rollers_EP-(OIA90)-WEB-FLAC-2025.rar'

so pyload fails to decode the Content-Disposition HTTP header

also, how can i use the download time to find the downloaded file?

    [2026-11-18 16:28:48]  INFO                pyload  Download finished: DÐ

## Response:

11/19/2026, 12:00:20 PM

Yes, the additional logs make the situation much clearer. There are **two separate problems**, and the timestamps give us a good way to locate the missing file.

## 1. The Content-Disposition header is incorrectly decoded

The original filename is correct when pyLoad extracts it from Rapidgator's webpage:

But when pyLoad processes the HTTP `Content-Disposition` header, it becomes:

This is consistent with UTF-8 bytes being decoded as Latin-1.

You can reverse that corruption:

However, I would fix this at the HTTP header parsing layer rather than unconditionally applying it to every filename. A properly decoded filename should not undergo that conversion.

Also, the log suggests that the corrupted filename may have replaced the original filename during the download.

## 2. Find the downloaded file using its timestamp

Your log gives us:

<box gap={1}>
  <row align="center" justify="between">
    <text color="secondary" size="xs">Download started</text>
    **16:27:37**
  </row>
  <row align="center" justify="between">
    <text color="secondary" size="xs">Chunk finished</text>
    **16:27:41**
  </row>
  <row align="center" justify="between">
    <text color="secondary" size="xs">File saved</text>
    **16:28:48**
  </row>
</box>

There is an important detail: the `File saved` line at 16:28:48 belongs to a different downloader ID (`72612`), whereas the original DО download started with ID `72612` at 16:27:37.

Because the log is interleaved, **we cannot determine the exact completion time of the DО download from these lines alone**.

Nevertheless, we can search for files modified between 16:27 and 16:29 on November 18, 2026.

### Option A: Linux `find`

Use this first:

This searches recursively and shows:

- Modification timestamp
- File size in bytes
- Full filename

It will find files regardless of whether their names contain `OIA90`.

Note that `-newermt` uses the local timezone, and file modification times may differ from the log timestamps if the filesystem or application preserves another timestamp.

### Option B: Search by exact file size

This might be even more reliable.

Rapidgator reports the expected size:

Search for files with exactly that size:

This works even if the filename has been completely corrupted.

You can combine the size and time filters:

**I would start with this command.** It is the strongest search criterion available from your logs.

## 3. Python search that handles corrupted filenames

If the file has a strange name that your terminal cannot display correctly, this Python script will print the raw filesystem bytes.

Because `root` is a `bytes` object, `os.walk()` returns byte-based paths.

That means you can distinguish between:

This is particularly useful for debugging pyLoad's filename handling.

## 4. Another important clue: the extraction failures

Your logs show repeated failures:

Even for files without unusual characters, such as:

This suggests an additional problem unrelated to Unicode.

For example, pyLoad might be reporting files as successfully downloaded even though they are missing from the location expected by the extraction plugin.

I would verify one of the ordinary filenames first:

If that file does not exist either, the issue may be more fundamental than filename encoding.

It could be a mismatch between pyLoad's actual download destination and the destination used by `ExtractArchive`.

## 5. The most suspicious detail in your logs

Look at this sequence:

The downloader ID changes from `72612` to `72613`.

The same thing happens later:

This suggests that your logs are interleaved between concurrent downloads, or that pyLoad's downloader context is being reused or incorrectly associated with different files.

The second possibility would be particularly concerning if it also affects download paths.

We cannot establish which is happening without looking at the relevant code.

------------------------------------------------------------------------

## 6. What I would investigate next

The strongest approach is:

1.  Search for the file using its exact expected size, `149946368` bytes.
2.  Search by modification time around `2026-11-18 16:27:37` through `16:28:48`.
3.  Check whether the ordinary archives that failed extraction actually exist.
4.  Inspect the pyLoad code that parses `Content-Disposition` and selects the final filename.

One additional diagnostic: if the filesystem is Linux, use `stat` to compare the modification time (`mtime`) and inode change time (`ctime`). A rename generally updates `ctime`, but not `mtime`. This can help find a file that was downloaded earlier and renamed around 16:28:48.

**My current hypothesis:** pyLoad is receiving a valid UTF-8 filename, incorrectly decoding the `Content-Disposition` header, and potentially saving the file under that corrupted name. But the extraction failures for ASCII-only filenames suggest there may also be a separate download-path or file-lifecycle bug.

If the exact-size search returns nothing, I would next inspect pyLoad's `File saved` code path to determine what that message actually guarantees.

## Prompt:

11/19/2026, 12:23:26 PM

ok i found the file:

    $ ls D_Flair_M-I_-_Rollers_EP_2025_FLAC/
    'DÐ'$'\302\236''_Flair_and_MÐ¡-IÐ¡_-_Rollers_EP-(OIA90)-WEB-FLAC-2025.rar'

so, how can i fix this encoding bug in pyload?

as a quickfix, to fix at least the logging, i have modified pyload, to escape link names with "repr":

src/pyload/core/datatypes/pyfile.py

    def _set_size(self, value):
        self._size = int(value)

    def _set_name(self, value):
        self._name = purge.name(value, sep="")
        # repr: escape nonprintable chars for logging
        if self._name != repr(self._name):
            self._name = repr(self._name)

    class PyFile:
        """
        Represents a file object at runtime.
        """

        def __init__(
            self, manager, id, url, name, size, status, error, pluginname, package, order
        ):
            self.m = self.manager = manager
            self.m.cache[int(id)] = self

            self.id = int(id)
            self.url = url
            self._name = None
            self.name = name

            # repr: escape nonprintable chars for logging
            if self.name != repr(self.name):
                self.name = repr(self.name)

            self._size = None
            self.size = size

            self.status = status
            self.pluginname = pluginname
            self.packageid = package  #: should not be used, use package() instead
            self.error = error
            self.order = order
            # database information ends here

            self.lock = RLock()

            self.plugin = None
            # self.download = None

            self.wait_until = 0  #: time.monotonic() + time to wait

            # status attributes
            self.active = False  #: obsolete?
            self.abort = False
            self.reconnected = False

            self.statusname = None

            self.progress = 0
            self.maxprogress = 100

        # will convert all sizes to ints
        size = property(lambda self: self._size, _set_size)

        # ensure safe name assignment
        name = property(lambda self: self._name, _set_name)

but i want to fix the root problem, the broken decoding of the "Content-Disposition" HTTP header

the debug output

    [2026-11-18 16:27:37]  DEBUG               pyload  Content-Disposition: 'DÐ\x9e_Flair_and_MÐ¡-IÐ¡_-_Rollers_EP-(OIA90)-WEB-FLAC-2025.rar'

comes from

`self.log.debug(f"Content-Disposition: {filename!r}")`

in

src/pyload/core/network/http/http_chunk.py

    import codecs
    import os
    import re
    import time

    import pycurl

    from ...utils import web
    from .exceptions import WrongFormat
    from .http_request import HTTPRequest

    class ChunkInfo:
        def __init__(self, name):
            self.name = os.fsdecode(name)
            self.size = 0
            self.resume = False
            self.chunks = []
            self.loaded = False

        def __repr__(self):
            ret = f"ChunkInfo: {self.name}, {self.size}\n"
            for i, c in enumerate(self.chunks):
                ret += f"{i}# {c[1]}\n"
            return ret

        def set_size(self, size):
            self.size = int(size)

        def add_chunk(self, name, range):
            self.chunks.append((name, range))

        def clear(self):
            self.chunks = []

        def create_chunks(self, chunks):
            self.clear()
            chunk_size = self.size // chunks
            current = 0
            for i in range(chunks):
                end = self.size - 1 if (i == chunks - 1) else current + chunk_size
                self.add_chunk(f"{self.name}.chunk{i}", (current, end))
                current += chunk_size + 1

        def save(self):
            fs_name = f"{self.name}.chunks"
            with open(fs_name, mode="w", encoding="utf-8", newline="\n") as fh:
                fh.write(f"name:{self.name}\n")
                fh.write(f"size:{self.size}\n")
                for i, c in enumerate(self.chunks):
                    fh.write(f"#{i}:\n")
                    fh.write(f"\tname:{c[0]}\n")
                    fh.write(f"\trange:{c[1][0]}-{c[1][1]}\n")

        @staticmethod
        def load(name):
            fs_name = f"{name}.chunks"
            if not os.path.exists(fs_name):
                raise IOError
            with open(fs_name, encoding="utf-8") as fp:
                name_line = fp.readline()[:-1]
                size_line = fp.readline()[:-1]
                if name_line.startswith("name:") and size_line.startswith("size:"):
                    name = name_line[5:]
                    size = size_line[5:]
                else:
                    fp.close()
                    raise WrongFormat()
                save_folder = os.path.dirname(name)
                if (
                    not os.path.exists(save_folder)
                    and not os.path.isdir(save_folder)
                    or save_folder != os.path.dirname(fs_name)
                ):
                    raise IOError
                ci = ChunkInfo(name)
                ci.loaded = True
                ci.set_size(size)
                while True:
                    if not fp.readline():
                        break
                    name_line = fp.readline()[1:-1]
                    range_line = fp.readline()[1:-1]
                    if name_line.startswith("name:") and range_line.startswith("range:"):
                        chunk_name = name_line[5:]
                        chunk_range = range_line[6:].split("-")
                    else:
                        raise WrongFormat()

                    if save_folder != os.path.dirname(chunk_name):
                        raise IOError

                    ci.add_chunk(chunk_name, (int(chunk_range[0]), int(chunk_range[1])))

            return ci

        def remove(self):
            fs_name = f"{self.name}.chunks"
            if os.path.exists(fs_name):
                os.remove(fs_name)

        def get_count(self):
            return len(self.chunks)

        def get_chunk_filename(self, index):
            return self.chunks[index][0]

        def get_chunk_range(self, index):
            return self.chunks[index][1]

    class HTTPChunk:
        def __init__(self, id, parent, range=None, resume=False):
            self.id = id
            self.p = parent  #: HTTPDownload instance
            self.range = range  #: tuple (start, end)
            self.resume = resume

            # Chunk-specific state
            self.size = range[1] - range[0] if range else -1
            self.arrived = 0
            self.last_url = self.p.referer
            self.code = 0  #: last http code, set by parent
            self.aborted = False
            self.fp = None  #: file handle
            self.BOMChecked = False

            # # Speed calculation
            # self.sleep = 0.0
            # self.last_size = 0

            # Create wrapped HTTPRequest with parent's configuration
            self.request = HTTPRequest(cookies=self.p.cj, options=self.p.options)

            # Expose commonly used attributes from wrapped request
            self.c = self.request.c
            self.log = self.request.log

            # Chunk uses its own header buffer for parsing, but delegates to request's headers
            self._header_buffer = b""

            # Configure chunk-specific curl options
            self.c.setopt(pycurl.ENCODING, None)  #: avoid pycurl error 61

        def __repr__(self):
            return f"<HTTPChunk id={self.id}, size={self.size}, arrived={self.arrived}>"

        @property
        def cj(self):
            """Delegate to parent's cookie jar."""
            return self.p.cj

        @property
        def request_headers(self):
            """Delegate to wrapped request's headers."""
            return self.request.request_headers

        @property
        def response_headers(self):
            """Delegate to wrapped request's headers."""
            return self.request.response_headers

        def verify_header(self):
            return self.request.verify_header()

        def format_range(self):
            """Format HTTP Range header value for this chunk."""
            if self.id == len(self.p.info.chunks) - 1:
                end = ""
                start = self.arrived + self.range[0] if self.resume else self.range[0]
            else:
                end = min(self.range[1] + 1, self.p.size - 1)
                if self.id == 0 and not self.resume:
                    start = 0
                else:
                    start = self.arrived + self.range[0]
            return f"{start}-{end}"

        def get_handle(self):
            """
            Returns a configured Curl handle ready for perform/multiperform.
            """
            # Configure wrapped request for this transfer
            self.request.set_request_context(
                self.p.url, self.p.get, self.p.post, self.p.referer, self.p.cj
            )

            # Override with chunk-specific callbacks
            self.c.setopt(pycurl.WRITEFUNCTION, self._write_body_callback)
            self.c.setopt(pycurl.HEADERFUNCTION, self._write_header_callback)

            # Setup file I/O
            fs_name = self.p.info.get_chunk_filename(self.id)

            if self.resume:
                if not os.path.exists(fs_name):
                    raise pycurl.error(33)  #: simulate cannot resume
                self.fp = open(fs_name, mode="ab")
                self.arrived = self.fp.tell() or os.stat(fs_name).st_size

                if self.range:
                    if self.arrived + self.range[0] >= self.range[1]:
                        return None  #: chunk already finished

                    range_str = self.format_range()
                    self.log.debug(f"Chunk {self.id + 1} resuming with range {range_str}")
                    self.c.setopt(pycurl.RANGE, range_str)
                else:
                    self.log.debug(f"Resume File from {self.arrived}")
                    self.c.setopt(pycurl.RESUME_FROM, self.arrived)
            else:
                if self.range:
                    range_str = self.format_range()
                    self.log.debug(f"Chunk {self.id + 1} starting with range {range_str}")
                    self.c.setopt(pycurl.RANGE, range_str)
                self.fp = open(fs_name, mode="wb")

            return self.c

        def _write_header_callback(self, buf):
            """Handle incoming header data."""
            self._header_buffer += buf

            if not self.range and self._header_buffer.endswith(b"\r\n\r\n"):
                self.parse_header()
            elif not self.range and buf.startswith(b"150") and b"data connection" in buf:
                # FTP file size parsing
                size = re.search(rb"(\d+) bytes", buf)
                if size:
                    self.p.size = int(size.group(1))
                    self.p.chunk_support = True

        def _write_body_callback(self, buf):
            """Handle incoming body data with BOM stripping and rate limiting."""
            # Strip BOM on first chunk
            if not self.BOMChecked:
                if buf[:3] == codecs.BOM_UTF8:
                    buf = buf[3:]
                self.BOMChecked = True

            size = len(buf)
            self.arrived += size
            self.fp.write(buf)

            # Rate limiting
            if self.p.bucket:
                time.sleep(self.p.bucket.consumed(size))
            #
            # else:
            #     # Avoid small buffers, increasing sleep time slowly if buffer size gets smaller
            #     # otherwise reduce sleep time percentual (values are based on tests)
            #     # So in general cpu time is saved without reducing bandwidth too much
            #     if size < self.last_size:
            #         self.sleep += 0.002
            #     else:
            #         self.sleep *= 0.7
            #     self.last_size = size
            #     time.sleep(self.sleep)

            # Check if chunk is complete
            if self.range and self.arrived > self.size:
                self.aborted = True
                return 0  #: close transfer

            return None  #: continue

        def parse_header(self):
            """Parse response headers and update parent state."""
            self.response_headers.parse(self._header_buffer)

            self.p.chunk_support = self.response_headers.get("Accept-Ranges", "").lower() == "bytes"

            if not self.resume:
                content_len = self.response_headers.get("Content-Length")
                if content_len:
                    self.p.size = int(content_len)

            disposition_value = self.response_headers.get("Content-Disposition")
            if disposition_value:
                try:
                    location = self.response_headers.get("Location")
                    filename = web.parse.disposition(disposition_value, location, self.p.url)
                    if filename:
                        # no, this can make the logger hang at non-printable bytes
                        # self.log.debug(f"Content-Disposition: {filename}")
                        # FIXME handle encoding errors
                        self.log.debug(f"Content-Disposition: {filename!r}")
                        self.p.update_disposition(filename)
                except ValueError as exc:
                    self.log.warning(exc)

        def stop(self):
            """Stop download after next write_body call."""
            self.range = [0, 0]
            self.size = 0

        def reset_range(self):
            """
            Reset the range, so the download will load all data available.
            """
            self.range = None

        def set_range(self, range):
            """Set a new byte range for this chunk."""
            self.range = range
            self.size = range[1] - range[0]
            self.log.debug(f"Chunk {self.id + 1} range set to {self.format_range()}")

        def flush_file(self):
            """Flush and close file handle."""
            if self.fp:
                self.fp.flush()
                os.fsync(self.fp.fileno())
                self.fp.close()

        def close(self):
            """Clean up resources."""
            if self.fp:
                self.fp.close()
                self.fp = None

            if self.request:
                self.request.close()
                self.request = None
                self.c = None

how can i fix this encoding bug?

## Response:

11/19/2026, 12:23:27 PM

You found the root cause: **pyLoad is interpreting a UTF-8-encoded filename from the HTTP `Content-Disposition` header as Latin-1, producing mojibake.**

The correct fix belongs in `web.parse.disposition()` or the HTTP header decoding layer, **not in `PyFile._set_name()`**.

There is also a problem with your `repr()` workaround: it changes the actual filename, not just its logging representation.

## 1. Why the filename is corrupted

Your filesystem contains:

The original filename should be:

The corruption happens because these UTF-8 bytes:

are being interpreted as Latin-1:

The correct decoding is:

Strictly speaking, an HTTP `Content-Disposition` header's ordinary `filename=` parameter is traditionally interpreted as ISO-8859-1, while UTF-8 filenames should use the RFC 5987/6266 `filename*=` syntax.

But many servers send raw UTF-8 inside `filename=`, and download managers commonly need to accommodate that.

## 2. The immediate fix in `http_chunk.py`

You can repair the mojibake before passing the filename to `update_disposition()`.

Replace:

with:

Then retain:

This should fix your particular Rapidgator filename.

However, **this is a compatibility workaround, not a complete standards-compliant solution**.

For example, a valid Latin-1 filename containing `é` should remain unchanged. The code above handles that case when UTF-8 decoding fails, but some valid Latin-1 sequences can also form valid UTF-8, so automatic detection is inherently ambiguous.

More importantly, if the parser has already correctly decoded an RFC 5987 `filename*=UTF-8''...` value, you should not attempt to decode it again.

## 3. The better fix: inspect `web.parse.disposition()`

This function is where I would implement the permanent fix:

Find its definition:

Also inspect where HTTP response headers are converted from `bytes` into `str`:

There are two possible scenarios:

**Scenario A: `disposition_value` is already corrupted.**

For example:

This means the corruption occurred before `web.parse.disposition()` was called.

You would ideally preserve the original HTTP header bytes and parse them according to the header's declared encoding.

**Scenario B: `disposition_value` is correct, but `web.parse.disposition()` corrupts it.**

For example:

In that case, the bug is inside `web.parse.disposition()`.

To distinguish these cases, add:

If the raw header is already mojibake, inspect `self.response_headers.parse()`.

If the raw header is correct but the filename is corrupted, inspect `web.parse.disposition()`.

### A more robust decoding helper

For a parser that has already produced a Latin-1 representation of raw header bytes, you could use:

But apply this only to the legacy `filename=` parameter when you know the input is a Latin-1 representation of the header bytes.

For a permanent fix, the parser should:

1.  Prefer `filename*=` when present, respecting its declared charset.
2.  Handle ordinary `filename=` according to HTTP header conventions.
3.  Optionally detect raw UTF-8 in `filename=` for compatibility with servers such as Rapidgator.
4.  Preserve valid Latin-1 filenames when UTF-8 decoding fails.
5.  Sanitize the resulting filename before using it as a filesystem path.

For your case, the result should be:

## 4. Remove the `repr()` modification from `PyFile`

This part of your workaround is dangerous:

There are two issues.

First, `repr()` returns a Python string representation, including surrounding quotes and escape sequences.

For example:

Therefore:

is always true for ordinary strings.

Second, this means the actual filename can become something like:

including literal quote characters and backslashes.

Your `__init__()` also applies this transformation a second time, potentially introducing additional escaping.

Instead, restore:

And remove the additional `repr()` logic from `__init__()`.

For logging, escape the string only at the point where it is displayed:

Or use the existing `!r` formatting:

The latter is already correct for debugging.

If the logger truly hangs even when given `repr(filename)`, that is a separate problem worth investigating. The resulting string should not contain the original U+009E control character.

## 5. Rename the file you already downloaded

You can fix the existing filename without downloading the archive again.

Run this inside its directory:

This assumes the existing filename is exactly the Latin-1 mojibake shown in your log. It does not alter the archive's contents.

------------------------------------------------------------------------

## 6. One more thing: a potential logging bug

Your log line:

is interesting because it stops immediately before U+009E.

That suggests the logging output might be getting truncated or rejected at the control character.

However, `repr()` should escape U+009E as `\x9e`, so if your modified code still hangs, I would look for a different code path that logs the original filename.

You can find relevant logging statements with:

Also consider whether pyLoad's web UI, event system, or database serialization is processing the filename after logging.

A Python logger does not ordinarily terminate the process because it encounters a C1 control character.

## What I need to give you a proper patch

Please show me the implementations of:

and:

With those two functions, I can identify **exactly where the encoding goes wrong** and propose a minimal patch that fixes Rapidgator's raw UTF-8 headers without breaking correctly encoded filenames or RFC 5987 `filename*=` headers.

## Prompt:

11/19/2026, 12:33:34 PM

# Selected text:

## Selection 1

The better fix: inspect web.parse.disposition()

## My request:

src/pyload/core/utils/web/parse.py

    def disposition(disposition_value, location=None, fallback_url=None):
        """
        Extract and sanitize filename from a Content-Disposition header value.
        """
        def _extract_filename_star(_disposition_params):
            """Extract filename from filename* parameter (RFC 5987)."""
            if 'filename*' not in _disposition_params:
                return None

            _filename = _disposition_params['filename*']

            # Try RFC 2047 encoding
            m = re.search(r'=\?([^?]+)\?([QB])\?([^?]*)\?=', _filename, re.I)
            if m is not None:
                try:
                    data, encoding = parse_mime_header(_filename)[0]
                    return data.decode(encoding)
                except (LookupError, UnicodeEncodeError) as exc:
                    raise ValueError(f"Content-Disposition: | error: {exc}")

            # Try RFC 5987 encoding
            m = re.search(r'(.+?)\'(.*)\'(.+)', _filename)
            if m is not None:
                encoding, lang, data = m.groups()
                try:
                    return urllib.parse.unquote(data, encoding=encoding, errors="strict")
                except (LookupError, UnicodeDecodeError) as exc:
                    raise ValueError(f"Content-Disposition: | error: {exc}")

            return None

        def _extract_filename(_disposition_params):
            """Extract filename from filename parameter."""
            if 'filename' not in _disposition_params:
                return None

            _filename = _disposition_params['filename']

            # Try RFC 2047 encoding
            m = re.search(r'=\?([^?]+)\?([QB])\?([^?]*)\?=', _filename, re.I)
            if m is not None:
                try:
                    data, encoding = parse_mime_header(m.group(0))[0]
                    return data.decode(encoding)
                except (LookupError, UnicodeEncodeError) as exc:
                    raise ValueError(f"Content-Disposition: | error: {exc}")

            # Try URL decoding
            try:
                return urllib.parse.unquote(_filename, encoding="iso-8859-1", errors="strict")
            except UnicodeDecodeError:
                raise ValueError("Content-Disposition: | error: Error when decoding string from iso-8859-1.")

        def _extract_attachment_filename(_disposition_type, _location, _fallback_url):
            """Extract filename for attachment disposition type."""
            if _disposition_type.lower() != "attachment":
                return None

            if _location is not None:
                return parse_name(_location)
            elif _fallback_url is not None:
                return parse_name(_fallback_url)

            return None

        def _sanitize_filename(_filename):
            """Drop unsafe characters from filename."""
            _filename = posixpath_basename(_filename)
            _filename = ntpath_basename(_filename)
            _filename = safe_nm(_filename)
            _filename = _filename.lstrip('.')

            return _filename

        disposition_type, disposition_params = http_header(disposition_value)
        filename = (
            _extract_filename_star(disposition_params) or
            _extract_filename(disposition_params) or
            _extract_attachment_filename(disposition_type, location, fallback_url)
        )

        if filename:
            return _sanitize_filename(filename)

        return None

do you see any obvious bugs here?

## Response:

11/19/2026, 12:33:35 PM

Yes. There is one particularly obvious bug that explains your corrupted Rapidgator filename, plus a few other issues.

## 1. The main bug: hardcoded ISO-8859-1 decoding

This line in `_extract_filename()` is the likely culprit:

There are two problems:

**First:** `urllib.parse.unquote()` only decodes percent-encoded sequences. It does not repair characters that have already been decoded incorrectly.

For example:

So if `_filename` already contains mojibake, the function simply returns it unchanged.

**Second:** If the filename contains percent-encoded UTF-8, such as:

your code explicitly decodes it as ISO-8859-1:

Instead of:

This means your parser can produce exactly the corruption you're seeing.

However, the logs alone don't tell us whether Rapidgator sent raw UTF-8 bytes or percent-encoded UTF-8. We need to inspect the actual `disposition_value` to distinguish those cases.

## 2. Minimal fix for your specific problem

I would replace:

with:

This handles your example:

**Important:** This is a pragmatic UTF-8-first compatibility strategy. It is not strictly RFC-compliant for every possible legacy `filename=` value, and it assumes that the header parser represents raw header bytes using Latin-1.

Also, percent-decoding a plain `filename=` value is itself a compatibility choice: RFC 6266 warns that percent escapes in this parameter are handled inconsistently.

## 3. Other bugs in the function

### A. Incorrect exception handling for RFC 2047

You have:

But `.decode(encoding)` normally raises `UnicodeDecodeError`, not `UnicodeEncodeError`, when the byte sequence is invalid.

Change both occurrences to:

There is another potential issue:

If `parse_mime_header()` already returns a `str` for an unencoded segment, calling `.decode()` raises `AttributeError`.

You should check the return contract of `parse_mime_header()`.

### B. The RFC 5987 regex is too permissive

Current:

This is unanchored, accepts malformed values and requires at least one character of encoded filename data.

A better pattern is:

This handles:

and rejects unexpected text before or after the encoded value.

### C. The `filename*` RFC 2047 handling is questionable

RFC 5987's `filename*=` uses charset/language/percent-encoded data, not RFC 2047 encoded words.

You can support RFC 2047 as a compatibility extension, but I would not make it the primary interpretation of `filename*`.

### D. Filename precedence is correct

This part is good:

Preferring `filename*` over `filename` is consistent with RFC 6266.

One caveat: if `filename*` is malformed and raises `ValueError`, your code never tries the ordinary `filename` fallback.

------------------------------------------------------------------------

## 4. What I would change first

Before implementing a permanent fix, add this debug output immediately before `web.parse.disposition()`:

Then compare the result against these possibilities:

| Input                               | Meaning                             |
|-------------------------------------|-------------------------------------|
| `filename="DО_Flair..."`            | Already correctly decoded           |
| `filename="DÐ\x9e_Flair..."`        | Raw UTF-8 likely decoded as Latin-1 |
| `filename="D%D0%9E_Flair..."`       | Percent-encoded UTF-8               |
| `filename*=UTF-8''D%D0%9E_Flair...` | Correct RFC 5987 encoding           |

For the second case, the `latin-1` to `utf-8` conversion is appropriate.

For the third case, `urllib.parse.unquote(..., encoding="utf-8")` is sufficient.

For the fourth case, your existing `_extract_filename_star()` should already work.

**My recommendation:** Implement UTF-8-first decoding specifically in `_extract_filename()`, but first verify how `http_header()` handles the incoming header bytes. If that function already converts bytes into Unicode using UTF-8 or another encoding, we should fix the problem there rather than trying to reverse the conversion later.

Can you show the implementation of `http_header()`? That's the last piece needed to identify the correct decoding boundary.

## Prompt:

11/19/2026, 12:49:14 PM

with more debug prints in the HTTPChunk.parse_header function

    def parse_header(self):
        """Parse response headers and update parent state."""
        self.response_headers.parse(self._header_buffer)

        self.p.chunk_support = self.response_headers.get("Accept-Ranges", "").lower() == "bytes"

        if not self.resume:
            content_len = self.response_headers.get("Content-Length")
            if content_len:
                self.p.size = int(content_len)

        disposition_value = self.response_headers.get("Content-Disposition")
        if disposition_value:
            self.log.debug(f"HTTPChunk.parse_header: disposition_value={disposition_value!r}")
            try:
                location = self.response_headers.get("Location")
                self.log.debug(f"HTTPChunk.parse_header: location={location!r}")
                filename = web.parse.disposition(disposition_value, location, self.p.url)
                self.log.debug(f"HTTPChunk.parse_header: filename={filename!r}")
                if filename:
                    try:
                        filename_latin1_utf8 = filename.encode("latin-1").decode("utf-8")
                        self.log.debug(f"HTTPChunk.parse_header: filename_latin1_utf8={filename_latin1_utf8!r}")
                        filename = filename_latin1_utf8
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        pass
                    # no, this can make the logger hang at nonprintable bytes
                    # self.log.debug(f"Content-Disposition: {filename}")
                    # FIXME handle encoding errors
                    self.log.debug(f"Content-Disposition: {filename!r}")
                    self.p.update_disposition(filename)
            except ValueError as exc:
                self.log.warning(exc)

i get this debug output

    [2026-11-19 12:46:04]  DEBUG               pyload  HTTPChunk.parse_header: disposition_value='attachment; filename="DÐ\x9e_Flair_and_MÐ¡-IÐ¡_-_Rollers_EP-(OIA90)-WEB-FLAC-2025.rar"'
    [2026-11-19 12:46:04]  DEBUG               pyload  HTTPChunk.parse_header: location=None
    [2026-11-19 12:46:04]  DEBUG               pyload  HTTPChunk.parse_header: filename='DÐ\x9e_Flair_and_MÐ¡-IÐ¡_-_Rollers_EP-(OIA90)-WEB-FLAC-2025.rar'
    [2026-11-19 12:46:04]  DEBUG               pyload  HTTPChunk.parse_header: filename_latin1_utf8='DО_Flair_and_MС-IС_-_Rollers_EP-(OIA90)-WEB-FLAC-2025.rar'
    [2026-11-19 12:46:04]  DEBUG               pyload  Content-Disposition: 'DО_Flair_and_MС-IС_-_Rollers_EP-(OIA90)-WEB-FLAC-2025.rar'

so now, in this case, the resulting filename is correct, but i want a proper fix that also works for other filenames, ideally for all filenames.

this should be a long-solved problem, mostly, web browsers like chromium should handle all these cases correctly. so how can we properly fix pyload's "disposition" function?

## Response:

11/19/2026, 12:49:21 PM

> **Searched 5 websites**
>
> Worked for 6s

Your new debug output confirms that the mojibake is already present **before `web.parse.disposition()` is called**:

And this successfully recovers the original filename:

For a proper fix, I would follow the approach used by modern browsers: **preserve the original HTTP header bytes, parse `filename*` according to RFC 5987, and use a carefully defined fallback strategy for legacy `filename`.**

There is one unavoidable limitation: HTTP headers can contain filenames without an explicit charset. It is mathematically impossible to decode every such filename correctly because the same bytes can represent different characters in different encodings.

## 1. What browsers generally do

The relevant standard is <Link url="https://www.rfc-editor.org/rfc/rfc6266" title="RFC 6266 - Content-Disposition in HTTP"/>.

For filename extraction, the important cases are:

| Header syntax | Decoding strategy |
|----|----|
| `filename*=UTF-8''...` | Decode using declared UTF-8 charset |
| `filename*=ISO-8859-1''...` | Decode using declared Latin-1 charset |
| `filename="plain.rar"` | ASCII-compatible legacy filename |
| `filename="raw UTF-8 bytes"` | UTF-8 compatibility decoding |
| `filename="Latin-1 bytes"` | Legacy encoding fallback |
| `filename="percent%20encoded.rar"` | Browser-dependent compatibility behavior |
| `filename="=?UTF-8?B?...?="` | Nonstandard RFC 2047 compatibility handling |

Chromium and Firefox have accumulated compatibility rules for malformed server responses. Their behavior is not identical, and neither can infer arbitrary legacy encodings perfectly.

For pyLoad, a reasonable default is:

1.  Prefer a valid `filename*`.
2.  For legacy `filename`, try strict UTF-8 decoding of the original bytes.
3.  If UTF-8 fails, use ISO-8859-1 as a fallback.
4.  Apply any optional percent-decoding and RFC 2047 compatibility rules deliberately.
5.  Sanitize the resulting filename only after decoding.

The critical detail is that **you should decode the bytes, not try to guess whether an already-decoded Python string looks corrupted**.

## 2. Chromium's implementation is a useful reference

Chromium has a dedicated `HttpContentDisposition` parser with explicit support for:

- RFC 5987 extended filenames.
- RFC 2047 encoded words.
- Percent-encoded filenames.
- Non-ASCII legacy filenames.
- A referrer charset for interpreting ambiguous legacy bytes.

Its implementation also tracks which compatibility features were used. \<Cite refs={\["turn990114search14","turn990114search4"\]}/\>

You can inspect the actual implementation here:

<Link url="https://chromium.googlesource.com/chromium/src/+/refs/heads/main/net/http/http_content_disposition.cc" title="Chromium - http_content_disposition.cc"/>

An important nuance: Chromium's legacy handling is more sophisticated than simply trying UTF-8 and then Latin-1. It can use the referring page's character encoding for ambiguous cases.

For pyLoad, I would start with a smaller implementation and add compatibility rules as needed.

## 3. Proposed implementation for pyLoad

Since your `http_header()` already returns parameter strings, you can retain it and improve the filename decoding.

The following is a replacement for the two nested filename extraction helpers. It assumes that the HTTP header parser uses Latin-1 to preserve raw header bytes, as your debug output suggests.

<CodeBlock language="python" editable>
import re
import urllib.parse
from email.header import decode_header

def \_decode_legacy_filename(value):  
"""  
Decode a legacy Content-Disposition filename= value.

    Assumes raw HTTP header bytes were mapped to Unicode
    using ISO-8859-1, preserving their byte values.
    """
    # RFC 2047 compatibility (nonstandard for HTTP).
    if re.search(r"=\?[^?]+\?[bqBQ]\?[^?]*\?=", value):
        try:
            parts = decode_header(value)
            return "".join(
                part.decode(charset or "ascii")
                if isinstance(part, bytes) else part
                for part, charset in parts
            )
        except (UnicodeError, LookupError):
            pass

    # Recover the original header bytes.
    try:
        raw = value.encode("latin-1")
    except UnicodeEncodeError:
        # Input is already Unicode, not Latin-1-mapped bytes.
        return value

    # Browser compatibility: percent-encoded filenames.
    # Do not decode encoded path separators or NUL.
    if re.search(rb"%[0-9a-fA-F]{2}", raw):
        decoded = urllib.parse.unquote_to_bytes(raw)

        if not any(c in decoded for c in (b"/", b"\\", b"\x00")):
            raw = decoded

    # Prefer UTF-8 for raw non-ASCII bytes.
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        # Preserve Latin-1 legacy filenames.
        return raw.decode("latin-1")

def \_decode_extended_filename(value):  
"""  
Decode RFC 5987 filename\*=charset'language'value.  
"""  
match = re.fullmatch(r"(\[^'\]+)'(\[^'\]*)'(.*)", value)

    if not match:
        return None

    charset, language, encoded = match.groups()

    try:
        raw = urllib.parse.unquote_to_bytes(encoded)
        return raw.decode(charset, errors="strict")
    except (UnicodeError, LookupError):
        return None

</CodeBlock>

Then inside `disposition()`:

This is a practical compatibility implementation, not an exact port of Chromium.

There are a few important considerations before merging it:

- The percent-decoding rule is deliberately conservative, but it still changes literal `%XX` sequences in some filenames. You may want to make this configurable.
- The code assumes Latin-1 mapping at the HTTP header boundary. If that assumption changes, the decoding contract must change too.
- The current `http_header()` parser still needs to be checked for quoted semicolons, escaped quotes, duplicate parameters and malformed headers.
- Sanitization should also reject or replace control characters, path traversal components, and reserved filenames. Your existing `safe_nm()` may already handle some of these.

## 4. Tests I would add

These tests cover the most important cases, including your Rapidgator bug.

``` python
import pytest

@pytest.mark.parametrize(
    "header, expected",
    [
        (
            'attachment; filename="hello.rar"',
            "hello.rar",
        ),
        (
            'attachment; filename="DÐ\x9e_Flair.rar"',
            "DО_Flair.rar",
        ),
        (
            'attachment; filename="cafÃ©.rar"',
            "café.rar",
        ),
        (
            'attachment; filename="café.rar"',
            "café.rar",
        ),
        (
            "attachment; filename*=UTF-8''caf%C3%A9.rar",
            "café.rar",
        ),
        (
            "attachment; filename*=ISO-8859-1''caf%E9.rar",
            "café.rar",
        ),
        (
            'attachment; filename="fallback.rar"; '
            "filename*=UTF-8''correct%C3%A9.rar",
            "correcté.rar",
        ),
        (
            'attachment; filename="hello%20world.rar"',
            "hello world.rar",
        ),
    ],
)
def test_disposition(header, expected):
    assert disposition(header) == expected
```

The `café.rar` test is worth noting: it passes under both correctly decoded Unicode input and Latin-1 byte mapping, but other Unicode strings may not. That is why the input encoding contract matters.

## 5. My preferred architecture for pyLoad

I would separate the implementation into three layers:

<box border radius="lg" padding={3} gap={2}>
  <box background="surface-secondary" radius="md" padding={3} align="center" gap={1}>
    **HTTP response header parser**
    <text color="secondary" size="xs" textAlign="center">Preserve raw header bytes, or map them reversibly using Latin-1</text>
  </box>
  <row justify="center">
    <icon name="arrow-down" color="secondary"/>
  </row>
  <box background="surface-secondary" radius="md" padding={3} align="center" gap={1}>
    **`web.parse.disposition()`**
    <text color="secondary" size="xs" textAlign="center">Parse parameters, decode charsets, apply compatibility rules</text>
  </box>
  <row justify="center">
    <icon name="arrow-down" color="secondary"/>
  </row>
  <box background="surface-secondary" radius="md" padding={3} align="center" gap={1}>
    **Filename sanitization**
    <text color="secondary" size="xs" textAlign="center">Remove unsafe path components and filesystem-invalid characters</text>
  </box>
</box>

This avoids mixing HTTP encoding logic with filesystem handling or logging.

**One final recommendation:** Before adopting the patch above, inspect `http_header()`, particularly how it splits parameters and whether it performs any Unicode conversions.

Your debug output proves that the Latin-1-to-UTF-8 repair works for Rapidgator. It does not yet prove that the existing parser preserves all other header values reversibly.

That distinction is what determines whether this can be a general-purpose fix rather than another workaround.

## Prompt:

11/19/2026, 12:57:35 PM

the "`safe_nm`" function is

src/pyload/core/utils/web/parse.py

    from ..purge import name as safe_nm

src/pyload/core/utils/purge.py

    def name(text, sep="_", allow_whitespaces=True):
        """Remove invalid characters."""
        bc = uniquify(_WINBADCHARS + _MACBADCHARS + _UNIXBADCHARS)
        repl = r"".join(bc)
        if not allow_whitespaces:
            repl += " "
        res = chars(text, repl, sep).strip()
        if res.lower() in _WINBADWORDS:
            res = (sep or "_") + res
        return res

and the full

src/pyload/core/utils/purge.py

is

    import re

    def chars(text, chars, repl=""):
        """
        Removes all chars in repl from text.
        """
        chars = chars.replace("\\", "\\\\")
        return re.sub(rf"[{chars}]", repl, text)

    _UNIXBADCHARS = ("\0", "/", "\\")
    _MACBADCHARS = _UNIXBADCHARS + (":",)
    _WINBADCHARS = _MACBADCHARS + ("<", ">", '"', "|", "?", "*")
    _WINBADWORDS = (
        "com1",
        "com2",
        "com3",
        "com4",
        "com5",
        "com6",
        "com7",
        "com8",
        "com9",
        "lpt1",
        "lpt2",
        "lpt3",
        "lpt4",
        "lpt5",
        "lpt6",
        "lpt7",
        "lpt8",
        "lpt9",
        "con",
        "prn",
    )

    def name(text, sep="_", allow_whitespaces=True):
        """Remove invalid characters."""
        bc = uniquify(_WINBADCHARS + _MACBADCHARS + _UNIXBADCHARS)
        repl = r"".join(bc)
        if not allow_whitespaces:
            repl += " "
        res = chars(text, repl, sep).strip()
        if res.lower() in _WINBADWORDS:
            res = (sep or "_") + res
        return res

    def pattern(text, rules):
        for rule in rules:
            try:
                pattr, repl, flags = rule
            except ValueError:
                pattr, repl = rule
                flags = 0
            text = re.sub(pattr, repl, text, flags)
        return text

    def truncate(text, to_length):
        min_length = len(text) // 2
        if to_length <= min_length:
            raise OSError("File name too long")
        offset = to_length // 3
        return f"{text[:offset * 2]}~{text[-(offset - 1 + to_length % 3):]}"

    def uniquify(seq):
        """Remove duplicates from seq preserving order."""

        seen = set()

        def make_hashable(item):
            if isinstance(item, list):
                return tuple(make_hashable(x) for x in item)
            elif isinstance(item, dict):
                return tuple(sorted((k, make_hashable(v)) for k, v in item.items()))
            elif isinstance(item, set):
                return tuple(sorted(make_hashable(x) for x in item))
            return item

        return type(seq)(x for x in seq if not (make_hashable(x) in seen or seen.add(make_hashable(x))))

does that help us with decoding?

i guess no, because purge.name only escapes special characters like "\|" or "?"

## Response:

11/19/2026, 12:57:36 PM

Correct. **`purge.name()` does not help with decoding.** It only sanitizes filenames after they have been decoded.

In your case, the filename passes through these stages:

The problem is that `purge.name()` preserves the mojibake rather than correcting it.

### One additional issue with `purge.name()`

It doesn't remove Unicode control characters, including U+009E, which appears in your corrupted filename.

Its prohibited characters are:

Therefore:

That's why the problematic control character survives into the filename and potentially into logging or the web interface.

You could improve sanitization by removing Unicode control characters:

However, **do not use this to fix your Rapidgator filename before decoding**. It would remove the U+009E character, destroying information needed to recover the original UTF-8 bytes.

### Another subtle issue: `purge.name()` is not a complete Windows filename sanitizer

It handles reserved names such as `CON` and `PRN`, but it doesn't correctly handle reserved names with extensions:

It also doesn't explicitly handle trailing dots or Unicode control characters.

Those are separate improvements worth making, but they don't belong in the HTTP filename decoding patch.

## What I'd do next

Keep `purge.name()` unchanged while fixing the encoding bug.

The remaining function I would inspect is:

And, ideally, the method that parses the raw header bytes:

Your debug output already shows that the header is corrupted before `disposition()` receives it. But that is not necessarily a bug in the header parser: **Latin-1 decoding can be a deliberate, reversible way to represent arbitrary HTTP header bytes.**

If the header parser uses Latin-1 consistently, we can implement a proper UTF-8-first legacy filename decoder in `disposition()` without changing the header parser at all.

That would be my preferred solution, with separate tests for UTF-8, Latin-1, RFC 5987, RFC 2047 and percent-encoded filenames.

## Prompt:

11/19/2026, 1:12:54 PM

> 3\. Proposed implementation for pyLoad

i have turned your proposed changes into a minimal-diff version:


    if 1: # keep indent
        def _extract_filename_star(_disposition_params):
            """Extract filename from filename* parameter (RFC 5987)."""
            if 'filename*' not in _disposition_params:
                return None

            _filename = _disposition_params['filename*']
            if 1:
                # TODO how is this better?!
                match = re.fullmatch(r"([^']+)'([^']*)'(.*)", _filename)
                if not match:
                    return None
                charset, language, encoded = match.groups()
                try:
                    raw = urllib.parse.unquote_to_bytes(encoded)
                    return raw.decode(charset, errors="strict")
                except (UnicodeError, LookupError):
                    return None
            # Try RFC 2047 encoding
            m = re.search(r'=\?([^?]+)\?([QB])\?([^?]*)\?=', _filename, re.I)
            if m is not None:
                try:
                    data, encoding = parse_mime_header(_filename)[0]
                    return data.decode(encoding)
                except (LookupError, UnicodeEncodeError) as exc:
                    raise ValueError(f"Content-Disposition: | error: {exc}")

            # Try RFC 5987 encoding
            m = re.search(r'(.+?)\'(.*)\'(.+)', _filename)
            if m is not None:
                encoding, lang, data = m.groups()
                try:
                    return urllib.parse.unquote(data, encoding=encoding, errors="strict")
                except (LookupError, UnicodeDecodeError) as exc:
                    raise ValueError(f"Content-Disposition: | error: {exc}")

            return None

        def _extract_filename(_disposition_params):
            """Extract filename from filename parameter."""
            if 'filename' not in _disposition_params:
                return None

            _filename = _disposition_params['filename']

            if 1:
                # TODO how is this better?!
                # RFC 2047 compatibility (nonstandard for HTTP).
                if re.search(r"=\?[^?]+\?[bqBQ]\?[^?]*\?=", _filename):
                    try:
                        parts = decode_header(value)
                        return "".join(
                            part.decode(charset or "ascii")
                            if isinstance(part, bytes) else part
                            for part, charset in parts
                        )
                    except (UnicodeError, LookupError):
                        pass

                # Recover the original header bytes.
                try:
                    raw = _filename.encode("latin-1")
                except UnicodeEncodeError:
                    # Input is already Unicode, not Latin-1-mapped bytes.
                    return _filename

                # Browser compatibility: percent-encoded filenames.
                # Do not decode encoded path separators or NUL.
                if re.search(rb"%[0-9a-fA-F]{2}", raw):
                    decoded = urllib.parse.unquote_to_bytes(raw)

                    if not any(c in decoded for c in (b"/", b"\\", b"\x00")):
                        raw = decoded

                # Prefer UTF-8 for raw non-ASCII bytes.
                try:
                    return raw.decode("utf-8")
                except UnicodeDecodeError:
                    # Preserve Latin-1 legacy filenames.
                    return raw.decode("latin-1")

            # Try RFC 2047 encoding
            m = re.search(r'=\?([^?]+)\?([QB])\?([^?]*)\?=', _filename, re.I)
            if m is not None:
                try:
                    data, encoding = parse_mime_header(m.group(0))[0]
                    return data.decode(encoding)
                except (LookupError, UnicodeEncodeError) as exc:
                    raise ValueError(f"Content-Disposition: | error: {exc}")

            # Try URL decoding
            try:
                return urllib.parse.unquote(_filename, encoding="iso-8859-1", errors="strict")
            except UnicodeDecodeError:
                raise ValueError("Content-Disposition: | error: Error when decoding string from iso-8859-1.")

        def _extract_attachment_filename(_disposition_type, _location, _fallback_url):
            """Extract filename for attachment disposition type."""
            if _disposition_type.lower() != "attachment":
                return None

            if _location is not None:
                return parse_name(_location)
            elif _fallback_url is not None:
                return parse_name(_fallback_url)

            return None

        def _sanitize_filename(_filename):
            """Drop unsafe characters from filename."""
            _filename = posixpath_basename(_filename)
            _filename = ntpath_basename(_filename)
            _filename = safe_nm(_filename)
            _filename = _filename.lstrip('.')

            return _filename

    def disposition(disposition_value, location=None, fallback_url=None):
        """
        Extract and sanitize filename from a Content-Disposition header value.
        """
        disposition_type, disposition_params = http_header(disposition_value)
        filename = (
            _extract_filename_star(disposition_params) or
            _extract_filename(disposition_params) or
            _extract_attachment_filename(disposition_type, location, fallback_url)
        )

        if filename:
            return _sanitize_filename(filename)

        return None

now please explain exactly why your changes are better than the original version

## Response:

11/19/2026, 1:12:55 PM

The changes improve three things: handling Rapidgator's raw UTF-8 filenames, decoding RFC 5987 filenames more precisely, and recovering from malformed headers.

However, **not every change is necessarily better than the original**, and I would revise parts of my earlier proposal before merging it into pyLoad.

First, there's an actual bug in the code you pasted:

`value` should be `_filename`:

Otherwise, unless `value` happens to exist in an enclosing scope, you'll get a `NameError`, which your exception handler won't catch.

## 1. `_extract_filename_star()`: why the new code is better

### Original

### New

There are three differences.

**A. `fullmatch()` rejects malformed input**

The original uses `re.search()`, which accepts a valid-looking substring anywhere in the value.

For example:

The original may find `UTF-8''hello.txt` within the string and treat it as valid.

The new version requires the entire string to match the expected structure.

**B. The new regex handles empty filenames**

The original `(.+)` requires at least one character after the second apostrophe.

The new `(.*)` permits an empty encoded value. An empty filename will subsequently be rejected by your existing fallback logic, but the parsing itself is more faithful to the grammar.

**C. Decoding bytes explicitly makes the charset handling clearer**

The original:

and the new:

are effectively equivalent for ordinary ASCII percent-encoded RFC 5987 values.

The new version separates percent-decoding from character decoding, which makes it easier to validate the raw bytes and diagnose failures.

**But:** The new version is not universally better if `encoded` already contains non-ASCII characters. `unquote_to_bytes()` encodes those characters as UTF-8 before percent-decoding, whereas `unquote()` preserves unescaped Unicode characters. A standards-conforming `filename*` value should be ASCII-only, so I would explicitly validate that rather than silently reinterpret it.

### One regression in the proposed replacement

Your original function also supports RFC 2047 encoded words inside `filename*`.

The replacement removes that support.

RFC 2047 is not the proper syntax for `filename*`, so this is defensible for standards compliance, but it could break compatibility with malformed servers.

If compatibility is your priority, preserve the RFC 2047 fallback after attempting valid RFC 5987 decoding.

## 2. `_extract_filename()`: why the new code fixes Rapidgator

This is the most important change.

### Original

### New

The original cannot repair your filename because `urllib.parse.unquote()` only decodes percent escapes.

Your input is:

There are no percent escapes to decode.

The original returns exactly the same corrupted string.

The new code reverses the Latin-1 mapping:

Then decodes those bytes as UTF-8:

This is precisely why your Rapidgator filename is repaired.

### What happens with other encodings?

| Original bytes       | Intended text      | New behavior                 |
|----------------------|--------------------|------------------------------|
| `b'hello.rar'`       | ASCII              | Correct                      |
| `b'caf\xc3\xa9.rar'` | UTF-8 `café.rar`   | Correct                      |
| `b'caf\xe9.rar'`     | Latin-1 `café.rar` | Correct, via fallback        |
| `b'\xd0\x9e.rar'`    | UTF-8 `О.rar`      | Correct                      |
| `b'\xc3\xa9.rar'`    | Latin-1 `Ã©.rar`   | Interpreted as UTF-8 `é.rar` |

The last row illustrates the unavoidable ambiguity.

**UTF-8-first decoding is a compatibility policy, not a guaranteed way to identify the original encoding.**

For a download manager serving modern websites, it is a reasonable default.

## 3. RFC 2047: the new approach is more complete, but needs fixing

### Original

### New

The important improvement is that `email.header.decode_header()` can handle **multiple encoded words and surrounding plain text**.

For example:

The original searches for one encoded word and returns only that word's decoded content.

It can lose the surrounding `report_` prefix and `.rar` suffix.

The new approach processes the complete filename and reconstructs it.

That is a meaningful improvement.

However, I would change the implementation to:

``` python
from email.header import decode_header

def _decode_rfc2047(value):
    parts = decode_header(value)

    return "".join(
        part.decode(charset or "ascii", errors="strict")
        if isinstance(part, bytes)
        else part
        for part, charset in parts
    )
```

And catch:

This avoids the original's incorrect `UnicodeEncodeError`-only handling.

## 4. Percent-encoded filenames: the proposed change is debatable

My earlier proposal included:

The intention was to avoid turning an encoded path separator into an actual path separator.

For example:

Should that mean:

or literally:

RFC 6266 specifically warns about inconsistent handling of percent escapes in ordinary `filename=` parameters.

The original pyLoad code always percent-decodes them.

My proposed code decodes them conditionally.

That is a behavior change, and it is not automatically better.

There is also a weakness in my implementation: it checks the entire decoded filename for `/`, `\`, or NUL, not just whether decoding introduced those characters. That can suppress otherwise harmless decoding when the original string already contains such a character.

**For a minimal-diff pyLoad patch, I would preserve the existing percent-decoding behavior initially.** Fix the character encoding separately, then decide whether to change percent-escape handling in another patch.

## 5. One important problem with your current `if 1` structure

Your current code:

means the original implementation below it is unreachable in normal execution.

In `_extract_filename_star()`, every path through the new block returns or raises, so the original RFC 2047 and RFC 5987 handling never executes.

In `_extract_filename()`, the same is true, apart from an unexpected exception.

Therefore, this is not a fallback-based implementation. It is a complete replacement with dead code retained underneath.

That's fine for experimentation, but it makes comparing behavior more confusing.

## 6. What I would actually merge into pyLoad

For the specific encoding bug, I would make a smaller change than my previous proposal.

Keep the existing RFC 2047 handling and the existing `filename*` implementation for now.

Replace only the legacy filename URL-decoding section with:

This gives you the core fix:

- Raw UTF-8 filenames work.
- Percent-encoded UTF-8 filenames work.
- Legacy Latin-1 filenames still work when their bytes are not valid UTF-8.
- ASCII filenames remain unchanged.
- The existing RFC 2047 and RFC 5987 logic is preserved.

It also avoids introducing unrelated behavioral changes into the same patch.

The main assumption remains that `http_header()` passes through the Latin-1-mapped header bytes. Your Rapidgator logs strongly support that assumption, but inspecting the function would confirm it.

### My assessment

| Change | Worth keeping? |
|----|----|
| UTF-8-first decoding of legacy `filename=` | **Yes - fixes your bug** |
| Latin-1 fallback | **Yes - preserves legacy compatibility** |
| `re.fullmatch()` for RFC 5987 | Yes |
| Explicit bytes decoding for RFC 5987 | Optional |
| `decode_header()` for RFC 2047 | Yes, with the variable-name fix |
| Conditional percent-decoding | Not yet; separate compatibility decision |
| Returning `None` for malformed `filename*` | Yes, allows fallback to `filename` |

**I would submit the UTF-8-first legacy decoding change as the first pyLoad patch**, with regression tests for your Rapidgator filename, Latin-1, ASCII, percent-encoded UTF-8, and RFC 5987. Then improve the parser's standards compliance in a separate change.

## Prompt:

11/19/2026, 2:08:00 PM

ok, but what i still dont understand is this:

`raw = _filename.encode("latin-1")`

should always succeed, because this simply turns a string into a bytestring, preserving all original bytes, because in the latin1 encoding, all 255 possible byte values are valid (?), so the `except UnicodeEncodeError` branch is never reached (?)


    def _extract_filename(_disposition_params):
        """Extract filename from filename parameter."""
        if 'filename' not in _disposition_params:
            return None

        _filename = _disposition_params['filename']

        # Try RFC 2047 encoding
        # old code
        r'''
        m = re.search(r'=\?([^?]+)\?([QB])\?([^?]*)\?=', _filename, re.I)
        if m is not None:
            try:
                data, encoding = parse_mime_header(m.group(0))[0]
                return data.decode(encoding)
            except (LookupError, UnicodeEncodeError) as exc:
                raise ValueError(f"Content-Disposition: | error: {exc}")
        '''
        # new code
        # TODO how is this better than the old code
        # RFC 2047 compatibility (nonstandard for HTTP).
        if re.search(r"=\?[^?]+\?[bqBQ]\?[^?]*\?=", _filename):
            try:
                parts = decode_header(_filename)
                return "".join(
                    part.decode(charset or "ascii")
                    if isinstance(part, bytes) else part
                    for part, charset in parts
                )
            except (UnicodeError, LookupError):
                pass

        # # Try URL decoding
        # if _filename already contains non-ASCII characters:
        # - unquote_to_bytes encodes those characters as UTF-8 before percent-decoding.
        # - unquote preserves unescaped Unicode characters.
        # FIXME urllib.parse.unquote only decodes percent escapes.
        # old code
        r'''
        try:
            return urllib.parse.unquote(_filename, encoding="iso-8859-1", errors="strict")
        except UnicodeDecodeError:
            raise ValueError("Content-Disposition: | error: Error when decoding string from iso-8859-1.")
        '''
        # new code ...

        # Recover the original header bytes.
        try:
            # example:
            # _filename =  '\xd0\x9e'
            # raw       = b'\xd0\x9e'
            # utf8_str  =  '\u041e'
            raw = _filename.encode("latin-1")
        except UnicodeEncodeError:
            # Input is already Unicode, not Latin-1-mapped bytes.
            return _filename

        # Browser compatibility: percent-encoded filenames.
        # Do not decode encoded path separators or NUL.
        if re.search(rb"%[0-9a-fA-F]{2}", raw):
            decoded = urllib.parse.unquote_to_bytes(raw)

            if not any(c in decoded for c in (b"/", b"\\", b"\x00")):
                raw = decoded

        # Prefer UTF-8 for raw non-ASCII bytes.
        try:
            utf8_str = raw.decode("utf-8")
            return utf8_str
        except UnicodeDecodeError:
            # Preserve Latin-1 legacy filenames.
            latin1_str = raw.decode("latin-1")
            return latin1_str

## Response:

11/19/2026, 2:08:04 PM

You're almost correct. The important distinction is:

**Latin-1 can decode every possible byte value, but it cannot encode every possible Unicode character.**

These are two different operations.

## 1. Latin-1 decoding always succeeds

Latin-1 (ISO-8859-1) maps all **256 possible byte values**, from `0x00` to `0xFF`, directly to Unicode code points U+0000 through U+00FF.

Therefore:

And the operation is perfectly reversible:

This is why HTTP header parsers often use Latin-1: it allows arbitrary header bytes to be represented as Python strings without losing information.

## 2. Latin-1 encoding can fail

Python strings are Unicode, not byte arrays. They can contain characters outside Latin-1's 256-character repertoire.

For example:

Notice that these two characters look somewhat similar but are different:

| Character                | Unicode | Latin-1 encodable? |
|--------------------------|---------|--------------------|
| `Ð` (Latin capital Eth)  | U+00D0  | Yes                |
| `О` (Cyrillic capital O) | U+041E  | No                 |
| `é`                      | U+00E9  | Yes                |
| `€`                      | U+20AC  | No                 |
| `😀`                     | U+1F600 | No                 |

Therefore, your exception handler is reachable:

For example, if `_filename` is already correctly decoded:

then `.encode("latin-1")` raises `UnicodeEncodeError`, and the function returns the correct filename unchanged.

## 3. Why the distinction matters for pyLoad

Consider these two inputs:

<box border radius="lg" padding={3} gap={3}>
  <box gap={1}>
    **Case A - Latin-1-mapped UTF-8 header**

    ```python
    _filename = "DÐ\x9e_Flair.rar"

    raw = _filename.encode("latin-1")
    # b'D\xd0\x9e_Flair.rar'

    raw.decode("utf-8")
    # 'DО_Flair.rar'
    ```

    <badge color="success">Recovered successfully</badge>

  </box>
  <divider color="subtle"/>
  <box gap={1}>
    **Case B - Already correctly decoded Unicode**

    ```python
    _filename = "DО_Flair.rar"

    raw = _filename.encode("latin-1")
    # Raises UnicodeEncodeError
    ```

    The exception handler returns `_filename` unchanged.

  </box>
</box>

So your exception handler is useful as a fallback when the input contains characters outside Latin-1.

## 4. But there is a subtle limitation

The check does **not** reliably distinguish mojibake from correctly decoded Unicode.

Consider a filename that is already correctly decoded:

It is entirely valid Unicode, but every character is also representable in Latin-1.

Therefore:

UTF-8 decoding fails, so the fallback returns the original string.

That happens to work.

But consider:

This could be a legitimate filename containing the two literal characters `Ã` and `©`.

Your code does this:

It silently changes the filename.

This is unavoidable if you attempt to detect encoding solely from the characters in an already-decoded string.

**The correct solution is to establish an explicit contract:** `http_header()` must provide a Latin-1 mapping of the original HTTP header bytes, and `_extract_filename()` interprets those bytes according to a documented policy.

With that contract, the UTF-8-first approach is predictable.

## 5. One improvement to your current implementation

Your current exception handler:

is reasonable for defensive compatibility, but it skips percent-decoding when the input is already Unicode.

For example:

It returns:

rather than:

If you want to preserve the existing percent-decoding behavior in this branch, use:

But again, this is a compatibility policy, not a universal decoding rule.

### My recommendation

Since your debug output confirms that Rapidgator's filename arrives as Latin-1-mapped UTF-8, I would use:

as the **minimal fix for raw UTF-8 headers**.

Then handle percent escapes separately, preserving pyLoad's existing behavior if required.

The key takeaway is that `.decode("latin-1")` can never fail for arbitrary bytes, but `.encode("latin-1")` absolutely can fail for arbitrary Unicode strings.

------------------------------------------------------------------------

Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)
