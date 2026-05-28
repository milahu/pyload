# -*- coding: utf-8 -*-

# TODO retry loop
# some challenges are hard to solve
# so it can be faster to give up and try a new challenge

# based on
# https://filecrypt.cc/js/pow_captcha_worker.js?v=25
# which is similar to
# https://github.com/sequentialread/pow-bot-deterrent/blob/main/static/proofOfWorker.js

# test:
# python -m src.pyload.plugins.anticaptchas.POWCaptchaFilecryptCc

import io
import os
import re
import urllib.parse
import hashlib
import math
import multiprocessing
import queue
import psutil
import time
import base64
import random
import json

# from pyload.core.utils.misc import eval_js

if __name__ == "__main__":
    import sys
    # fix: ModuleNotFoundError: No module named 'pyload'
    sys.path.insert(0, os.path.dirname(__file__) + "/../../..")
    # fix: ImportError: cannot import name 'str_exc' from partially initialized module 'src.pyload.plugins.helpers'
    from ... import core as pyload_core

from ..base.captcha_service import CaptchaService


class POWCaptchaFilecryptCc(CaptchaService):
    __name__ = "POWCaptchaFilecryptCc"
    __type__ = "anticaptcha"
    __version__ = '0.1'
    __status__ = "testing"

    __description__ = "POWCaptcha solver for FilecryptCc"
    __license__ = "MIT"
    __authors__ = [
        ("milahu", "milahu@milahu.duckdns.org"),
    ]

    # <input type="hidden" name="pow_id" value="08CA3A81FD">
    POW_ID_PATTERN = r'<input type="hidden" name="pow_id" value="([^"]+)">'

    # data-challenge="4bff2e1ad7bf1aa1108c1d44c77266c2"
    POW_CHALLENGE_PATTERN = r'<div class="pow-captcha".*? data-challenge="([^"]+)"'

    # data-difficulty="16"
    POW_DIFFICULTY_PATTERN = r'<div class="pow-captcha".*? data-difficulty="([^"]+)"'

    # data-ext="/js/m.js?v=25"
    POW_EXT_PATTERN = r'<div class="pow-captcha".*? data-ext="([^"]+)"'

    def challenge(self, data):
        self.data = data
        self._get_pow_id()
        self._get_pow_challenge()
        self._get_pow_difficulty()
        self._get_pow_ext()
        self._get_pow_fingerprint_1()
        self._get_pow_fingerprint_2()
        def on_progress(progress=0, elapsed=0, hashrate=0, num_workers=0, **kwargs):
            self.log_debug(
                f"challenge:"
                f" progress={progress:.2%}"
                f" elapsed={elapsed:.2f}s"
                f" hashrate={(hashrate / 1E6):.2f}MH/s"
                # f" num_workers={num_workers}"
            )
        result = solve_pow_parallel(
            challenge=self.pow_challenge,
            difficulty=self.pow_difficulty,
            cpu_fraction=0, # use 1 physical core
            on_progress=on_progress,
        )
        self.log_debug(f"challenge: nonce=" + str(result["nonce"]))
        params = dict(
            pow_id=self.pow_id,
            # NOTE apparently pow_data is not always sent
            pow_data=self.pow_fingerprint_2,
            pow_nonce=result["nonce"],
            pow_elapsed=int(result["elapsed"] * 1000), # milliseconds
            pow_pauses=0,
            pow_x=self.pow_fingerprint_1,
        )
        # this is also logged later in FilecryptCc self.load
        # self.log_debug(f"challenge: params={params}")
        return params
        # result = self.decrypt_interactive(params, timeout=300)
        # return result

    def _get_pow_id(self):
        m = re.search(self.POW_ID_PATTERN, self.data, flags=re.DOTALL)
        if not m:
            raise ValueError("Not found POW_ID_PATTERN")
        self.pow_id = m.group(1)
        self.log_debug(f"pow_id: {self.pow_id}")
        return self.pow_id

    def _get_pow_challenge(self):
        m = re.search(self.POW_CHALLENGE_PATTERN, self.data, flags=re.DOTALL)
        if not m:
            raise ValueError("Not found POW_CHALLENGE_PATTERN")
        self.pow_challenge = m.group(1)
        self.log_debug(f"pow_challenge: {self.pow_challenge}")
        return self.pow_challenge

    def _get_pow_difficulty(self):
        m = re.search(self.POW_DIFFICULTY_PATTERN, self.data, flags=re.DOTALL)
        if not m:
            raise ValueError("Not found POW_DIFFICULTY_PATTERN")
        self.pow_difficulty = int(m.group(1))
        self.log_debug(f"pow_difficulty: {self.pow_difficulty}")
        return self.pow_difficulty

    def _get_pow_ext(self):
        m = re.search(self.POW_EXT_PATTERN, self.data, flags=re.DOTALL)
        if not m:
            raise ValueError("Not found POW_EXT_PATTERN")
        self.pow_ext = m.group(1)
        self.pow_ext_url = urllib.parse.urljoin(self.pyfile.url, self.pow_ext)
        # self.log_debug(f"pow_ext: {self.pow_ext}")
        self.log_debug(f"pow_ext_url: {self.pow_ext_url}")
        return self.pow_ext

    def _get_pow_fingerprint_1(self):
        # we have to fetch the fingerprint challenge
        # otherwise the server keeps sending captchas
        # but fetching it once is enough
        if not hasattr(self, "pow_ext_src"):
            self.pow_ext_src = self.load(self.pow_ext_url)
        # TODO this fingerprint can change in the future
        # see also
        # src/pyload/plugins/anticaptchas/POWCaptchaFilecryptCc_fingerprint.html
        self.pow_fingerprint_1 = "2.0.63.W1s2MDVdXQ==" # "2.0.63." + base64encode("[[605]]")
        return self.pow_fingerprint_1

        # no. eval_js fails to solve this challenge
        # because eval_js has no Web APIs
        # https://developer.mozilla.org/en-US/docs/Web/API
        # trying to run this in eval_js just hangs forever -> timeout
        r'''
        self.log_debug(f"pow_ext_src: {self.pow_ext_src[:100]!r}...")
        t1 = time.time()
        self.log_debug(f"pow_fingerprint: starting ...")
        pow_ext_path = f"/var/run/user/{os.getuid()}/pyload.{os.getpid()}.pow_ext.js"
        self.log_debug(f"pow_ext_path: {pow_ext_path}")
        with open(pow_ext_path, "w", encoding="utf8") as f:
            f.write(self.pow_ext_src)
        self.pow_fingerprint_1 = eval_js(f"{self.pow_ext_src}; await R()", timeout_seconds=5)
        dt = time.time() - t1
        self.log_debug(f"pow_fingerprint: {self.pow_fingerprint_1} in {dt:.2f} seconds")
        return self.pow_fingerprint_1
        '''

    def _get_pow_fingerprint_2(self):
        """
        this is another fingerprint...
        probably it is compared with pow_fingerprint_1

        TODO update pow_fingerprint_2_dict
        open a filecrypt container in chrome at an URL like
        https://filecrypt.cc/Container/1234567890.html?mirror=0
        open chrome devtools -> network tab
        manually solve the captcha
        look for a new network request with the same filename (1234567890.html?mirror=0)
        payload -> form data -> pow_data

        the pow_data string is a base64-encoded JSON string
        you can decode it like
        echo "eyJhIjoxfQo=" | base64 -d | jq | sed 's/: true/: True/g; s/: false/: False/g'

        hint: use "gron" to compare JSON objects
        https://github.com/tomnomnom/gron
        """
        mouse_x = random.randint(100, 700) # max range is about (0, 820)
        mouse_y = random.randint(50, 150) # max range is about (0, 190)
        pow_fingerprint_2_dict = {
            "x": mouse_x,
            "y": mouse_y,
            "click_x": mouse_x + random.randint(-50, 50),
            "click_y": mouse_y + random.randint(-30, 30),
            "moves": random.randint(50, 200),
            "is_touch": False,
            "workerData": {
                "webGLVendor": "Google Inc. (AMD)",
                "webGLRenderer": "ANGLE (AMD, AMD Radeon Graphics (radeonsi renoir ACO), OpenGL ES 3.2)",
                "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
                "languages": [
                    "en",
                ],
                "platform": "Linux x86_64",
                "hardwareConcurrency": 12, # CPU threads
                # bot check? CDP = chrome devtools protocol
                # "cdpCheck1": True,
                "cdpCheck1": False,
                "isSameAsMainJsContext": True
            },
            "ui": True,
            "ua": {
                "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
                "platform": "Linux x86_64",
                "languages": [
                    "en",
                ],
                "hardwareConcurrency": 12 # CPU threads
            },
            "usa": [
                1,
                1
            ],
            "tz": "Europe/Berlin",
            "ta": random.random() * 1000,
            "tb": random.random() * 10000,
        }

        pow_fingerprint_2 = base64.b64encode(json.dumps(pow_fingerprint_2_dict, separators=(',', ':')).encode("utf8")).decode("ascii")
        self.pow_fingerprint_2 = pow_fingerprint_2
        return pow_fingerprint_2


def sha1_leading_zero_bits(digest: bytes) -> int:
    bits = 0
    for b in digest:
        if b == 0:
            bits += 8
            continue
        bits += 8 - b.bit_length()
        return bits
    return 160


def compute_worker_count(cpu_fraction: float = 1.0) -> tuple[int, int]:
    """
    Determine worker count from physical CPU cores.

    cpu_fraction:
        1.0 = all physical cores
        0.5 = half
        0.25 = quarter
        etc.
    """
    physical_cores = psutil.cpu_count(logical=False)
    # fallback if platform cannot determine physical cores
    if physical_cores is None:
        physical_cores = psutil.cpu_count(logical=True) or 1
    workers = max(1, int(physical_cores * cpu_fraction))
    # never exceed physical core count
    workers = min(workers, physical_cores)
    return workers, physical_cores


def pow_worker(
    worker_idx: int,
    num_workers: int,
    step_size: int,
    challenge: str,
    difficulty: int,
    stop_event: multiprocessing.Event,
    result_queue: multiprocessing.Queue,
    progress_counter: multiprocessing.Value,
):
    r"""
    distribute load across workers

    example:
    num_workers = 2
    step_size = 3
    worker_idx=0: 0 1 2       6 7 8         12 13 14
    worker_idx=1:       3 4 5       9 10 11          15 16 17

    example:
    num_workers = 3
    step_size = 2
    worker_idx=0: 0 1         6 7           12 13
    worker_idx=1:     2 3         8 9             14 15
    worker_idx=2:         4 5         10 11             16 17
    """
    start = worker_idx * step_size
    end = start + step_size # NOTE end is exclusive
    step_shift = num_workers * step_size
    hashes = 0
    last_report = time.perf_counter()
    prefix = f"{challenge}:".encode()
    # loop ranges of nonces
    while not stop_event.is_set():
        # loop nonces
        for nonce in range(start, end):
            candidate = prefix + str(nonce).encode("ascii")
            digest = hashlib.sha1(candidate).digest()
            if sha1_leading_zero_bits(digest) < difficulty:
                continue
            # number of hashes since the last "progress_counter.value += 1"
            step_hashes = nonce - start + 1
            result = {
                "nonce": nonce,
                "step_hashes": step_hashes, # estimate total_hashes
                # "worker": worker_idx, # debug
                "hexdigest": digest.hex(), # debug
            }
            result_queue.put(result)
            stop_event.set()
            return
        with progress_counter.get_lock():
            progress_counter.value += 1
        start += step_shift
        end += step_shift


def solve_pow_parallel(
    challenge: str,
    difficulty: int,
    cpu_fraction: float = 1.0,
    num_workers: int | None = None,
    step_size: int = 100,
    report_progress_dt = 1.0,
    on_progress = None,
):
    """
    Parallel PoW solver.

    Args:
        challenge:
            challenge string

        difficulty:
            required leading zero bits

        cpu_fraction:
            fraction of physical CPU cores to use

        num_workers:
            explicit worker count override

        step_size:
            how many hashes should each worker compute
            before checking if other workers found a result

            a smaller step size means more overhead in multiprocessing
            a larger step size means more wasted hash calculations

            step_size: int = 1, # hashrate: 0.5 MH/s
            step_size: int = 10, # hashrate: 4.7 MH/s
            step_size: int = 100, # hashrate: 6.4 MH/s
            step_size: int = 1000, # hashrate: 6.5 MH/s
            step_size: int = 10000, # hashrate: 6.8 MH/s

        report_progress_dt:
            report progress every N seconds

        on_progress:
            callback function to report progress

            if the callback function returns False
            then the workers are stopped
    """
    physical_cores = psutil.cpu_count(logical=False)
    if physical_cores is None:
        physical_cores = psutil.cpu_count(logical=True) or 1
    if num_workers is None:
        num_workers, _ = compute_worker_count(cpu_fraction)
    num_workers = max(1, min(num_workers, physical_cores))
    # print(f"physical cores : {physical_cores}")
    # print(f"num_workers        : {num_workers}")
    # print(f"cpu fraction   : {cpu_fraction}")
    # print(f"difficulty     : {difficulty}")
    # print(f"challenge      : {challenge}")
    # print()
    start_time = time.perf_counter()
    stop_event = multiprocessing.Event()
    result_queue = multiprocessing.Queue()
    progress_counter = multiprocessing.Value("i", 0)
    proc_list = []
    for worker_idx in range(num_workers):
        proc = multiprocessing.Process(
            target=pow_worker,
            args=(
                worker_idx,
                num_workers,
                step_size,
                challenge,
                difficulty,
                stop_event,
                result_queue,
                progress_counter,
            ),
        )
        proc.start()
        proc_list.append(proc)
    total_hashes = 0
    last_report_progress = time.perf_counter()
    expected = 2 ** difficulty

    def default_on_progress(progress=0, elapsed=0, total_hashes=0, hashrate=0, num_workers=0, **kwargs):
        print(
            f"\r"
            f"progress={progress:.2%}"
            f" elapsed={elapsed:.2f}s"
            f" total_hashes={(total_hashes / 1E6):.2f}M"
            f" hashrate={(hashrate / 1E6):.2f}MH/s "
            f" num_workers={num_workers}"
            + " "*10,
            end="",
            flush=True,
        )

    if not callable(on_progress):
        on_progress = default_on_progress

    try:
        # monitor workers
        while True:
            if not result_queue.empty():
                # solved
                result = result_queue.get()
                elapsed = time.perf_counter() - start_time
                # estimate total_hashes
                total_hashes += result["step_hashes"] * num_workers
                del result["step_hashes"] # not useful
                hashrate = total_hashes / elapsed if elapsed else 0
                progress = 1 - math.exp(-total_hashes / expected)
                result["elapsed"] = elapsed
                result["total_hashes"] = total_hashes
                result["expected"] = expected
                result["progress"] = progress
                result["hashrate"] = hashrate
                return result
                break
            # not solved
            total_hashes = progress_counter.value * step_size
            now = time.perf_counter()
            if now - last_report_progress >= report_progress_dt:
                elapsed = now - start_time
                hashrate = total_hashes / elapsed if elapsed else 0
                progress = 1 - math.exp(-total_hashes / expected)
                should_continue = on_progress(
                    progress=progress,
                    elapsed=elapsed,
                    hashrate=hashrate,
                    total_hashes=total_hashes,
                    expected=expected,
                    num_workers=num_workers,
                    # TODO pass more kwargs to on_progress?
                )
                if should_continue == False:
                    # stop workers
                    return
                last_report_progress = now
            # wait for workers
            time.sleep(0.01)

    # except Exception as exc:
    #     print(f"FIXME: {type(exc).__name__}: {exc}")

    finally:
        stop_event.set()
        for proc in proc_list:
            proc.join()


if __name__ == "__main__":

    import json

    try:
        challenge = sys.argv[1]
    except IndexError:
        challenge = "4bff2e1ad7bf1aa1108c1d44c77266c2" # nonce: 33793

    try:
        difficulty = int(sys.argv[2])
    except IndexError:
        difficulty = 16 # elapsed: 0.02
        difficulty = 20 # elapsed: 0.8
        difficulty = 21 # elapsed: 1
        difficulty = 22 # elapsed: 4
        difficulty = 23 # elapsed: 5
        difficulty = 24 # elapsed: 7

    def on_progress(progress=0, elapsed=0, hashrate=0, num_workers=0, **kwargs):
        print(
            f"progress={progress:.2%}"
            f" elapsed={elapsed:.2f}s"
            f" hashrate={(hashrate / 1E6):.2f}MH/s"
            f" num_workers={num_workers}"
        )
        if 0:
            # test: should_continue == False
            if kwargs["progress"] > 0.95:
                print("giving up")
                return False

    result = solve_pow_parallel(
        challenge,
        difficulty,
        # cpu_fraction=0.5, # use 50% of physical cores
        # cpu_fraction=0, # use 1 physical core
        # report_progress_dt=0.5,
        # on_progress=on_progress,
    )

    print("\n" + "result: " + json.dumps(result, indent=2))
