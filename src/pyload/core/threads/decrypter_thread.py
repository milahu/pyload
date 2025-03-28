# -*- coding: utf-8 -*-


import os
import inspect


from ..network.exceptions import Abort, Fail, Retry
from .plugin_thread import PluginThread


class DecrypterThread(PluginThread):
    """
    thread for decrypting.
    """

    def __init__(self, manager, pyfile):
        """
        constructor.
        """
        super().__init__(manager)

        self.active = pyfile
        manager.local_threads.append(self)

        pyfile.set_status("decrypting")

        self.start()

    def get_active_files(self):
        return [self.active]

    def run(self):
        """
        run method.
        """
        pyfile = self.active
        retry = False

        try:
            self.pyload.log.info(
                self._("Decrypting starts: {}").format(self.active.name)
            )
            self.active.plugin.preprocessing(self)

        except NotImplementedError:
            self.pyload.log.error(
                self._("Plugin {} is missing a function").format(self.active.pluginname)
            )
            return

        except Fail as exc:
            msg = exc.args[0]

            if msg == "offline":
                self.active.set_status("offline")
                self.pyload.log.warning(
                    self._("Download is offline: {}").format(self.active.name)
                )
            else:
                self.active.set_status("failed")
                self.pyload.log.error(
                    self._("Decrypting failed: {name} | {msg}").format(
                        name=self.active.name, msg=msg
                    )
                )
                self.active.error = msg

            return

        except Abort:
            self.pyload.log.info(self._("Download aborted: {}").format(pyfile.name))
            pyfile.set_status("aborted")

            return

        except Retry:
            self.pyload.log.info(self._("Retrying {}").format(self.active.name))
            retry = True
            return self.run()

        except Exception as exc:
            self.active.set_status("failed")

            msg = str(exc)
            if msg == "":
                msg = type(exc).__name__
            else:
                msg = f"{type(exc).__name__}: {msg}"

            exc_trace = inspect.trace()
            exc_path = os.path.realpath(exc_trace[-1][1])
            exc_line = exc_trace[-1][2]
            exc_source = exc_trace[-1][4][0].strip()

            pyload_src_root = os.path.realpath(os.path.dirname(__file__) + "/../../..")
            if exc_path.startswith(pyload_src_root):
                exc_path = exc_path[(len(pyload_src_root) + 1):]

            msg += f" @ {exc_path} line {exc_line}: {exc_source}"

            self.pyload.log.warning(
                self._("Decrypting failed: {name} | {msg}").format(
                    name=self.active.name, msg=msg
                ),
                exc_info=self.pyload.debug > 1,
                stack_info=self.pyload.debug > 2,
            )
            self.active.error = type(exc).__name__ + ": " + str(exc)

            if self.pyload.debug:
                self.write_debug_report(pyfile)

            return

        finally:
            if not retry:
                self.active.release()
                self.active = False
                self.pyload.files.save()
                self.m.local_threads.remove(self)
                # exc_clear()

        # self.pyload.addon_manager.download_finished(pyfile)

        # self.m.local_threads.remove(self)
        # self.active.finish_if_done()
        if not retry:
            pyfile.delete()
