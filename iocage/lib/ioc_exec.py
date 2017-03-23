"""iocage exec module."""
from subprocess import CalledProcessError, Popen, STDOUT

from iocage.lib.ioc_common import checkoutput
from iocage.lib.ioc_json import IOCJson
from iocage.lib.ioc_list import IOCList
from iocage.lib.ioc_start import IOCStart
import iocage.lib.ioc_log as ioc_log


class IOCExec(object):
    """Run jexec with a user inside the specified jail."""

    def __init__(self, command, uuid, tag, path, host_user="root",
                 jail_user=None, plugin=False, skip=False):
        self.command = command
        self.uuid = uuid
        self.tag = tag
        self.path = path
        self.host_user = host_user
        self.jail_user = jail_user
        self.plugin = plugin
        self.skip = skip
        self.lgr = ioc_log.getLogger('ioc_exec')

    def exec_jail(self):
        # TODO: Exec fib support
        if self.jail_user:
            flag = "-U"
            user = self.jail_user
        else:
            flag = "-u"
            user = self.host_user

        status, _ = IOCList().list_get_jid(self.uuid)
        if not status:
            if not self.plugin and not self.skip:
                print("{} ({}) is not running, starting jail.".format(
                    self.uuid, self.tag))
            conf = IOCJson(self.path).json_load()

            if conf["type"] in ("jail", "plugin"):
                IOCStart(self.uuid, self.tag, self.path, conf, silent=True)
            elif conf["type"] == "basejail":
                raise RuntimeError(
                    "Please run \"iocage migrate\" before trying"
                    " to start {} ({})".format(self.uuid,
                                               self.tag))
            elif conf["type"] == "template":
                raise RuntimeError(
                    "Please convert back to a jail before trying"
                    " to start {} ({})".format(self.uuid,
                                               self.tag))
            else:
                raise RuntimeError("{} is not a supported jail type.".format(
                    conf["type"]
                ))
            print("\nCommand output:")

        if self.plugin:
            try:
                checkoutput(["jexec", flag, user, "ioc-{}".format(
                    self.uuid)] + list(self.command), stderr=STDOUT)
            except CalledProcessError as err:
                return err.output.decode("utf-8").rstrip()
        else:
            jexec = Popen(["jexec", flag, user, "ioc-{}".format(self.uuid)] +
                          list(self.command))
            msg, err = jexec.communicate()

            if err:
                return err
