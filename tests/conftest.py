import builtins
import os
import sys
import types
from collections import defaultdict

# pfb_unbound.py is designed to run inside Unbound's Python plugin loader,
# which injects Unbound-specific functions (log_info, log_err, …) and
# integer constants as module-level globals before executing the script.
# Provide no-op / sentinel stubs so the file can be imported in a plain
# Python environment for unit testing.
builtins.log_info = lambda msg: None
builtins.log_err = lambda msg: None
builtins.log_warn = lambda msg: None

# Unbound integer constants
builtins.RR_TYPE_A = 1
builtins.RR_TYPE_AAAA = 28
builtins.RR_TYPE_ANY = 255
builtins.RR_TYPE_CNAME = 5
builtins.RR_TYPE_DNAME = 39
builtins.RR_TYPE_SIG = 24
builtins.RR_TYPE_MX = 15
builtins.RR_TYPE_NS = 2
builtins.RR_TYPE_PTR = 12
builtins.RR_TYPE_SRV = 33
builtins.RR_TYPE_TXT = 16
builtins.RR_CLASS_IN = 1
builtins.PKT_QR = 0x8000
builtins.PKT_RA = 0x0080
builtins.PKT_RD = 0x0100
builtins.RCODE_NOERROR = 0
builtins.RCODE_NXDOMAIN = 3
builtins.MODULE_EVENT_NEW = 0
builtins.MODULE_EVENT_PASS = 1
builtins.MODULE_EVENT_MODDONE = 3
builtins.MODULE_FINISHED = 4
builtins.MODULE_WAIT_MODULE = 2
builtins.MODULE_ERROR = 5

# register_* stubs return True (success)
builtins.register_inplace_cb_reply = lambda *a: True
builtins.register_inplace_cb_reply_cache = lambda *a: True
builtins.register_inplace_cb_reply_local = lambda *a: True
builtins.register_inplace_cb_reply_servfail = lambda *a: True


class _DNSMessage:
    """Minimal stand-in for Unbound's DNSMessage.

    Records every instance on the class so tests can inspect the answer
    section of the reply that operate() built before it was discarded.
    """

    instances: list = []

    def __init__(self, qname, qtype, qclass, flags):
        self.qname = qname
        self.qtype = qtype
        self.qclass = qclass
        self.flags = flags
        self.answer = []
        self._qstate = None
        _DNSMessage.instances.append(self)

    def set_return_msg(self, qstate):
        self._qstate = qstate
        if getattr(qstate, 'return_msg', None) is None:
            qstate.return_msg = types.SimpleNamespace(
                rep=types.SimpleNamespace(security=0, an_numrrsets=0, rrsets=[]),
                qinfo=types.SimpleNamespace(qname_str=self.qname, qname_list=[]),
            )
        qstate.return_msg.rep.security = 2
        return True


builtins.DNSMessage = _DNSMessage

# Make pfb_unbound importable from its installed location within the repo.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'usr', 'local', 'pkg', 'pfblockerng'))

import pytest  # noqa: E402

import pfb_unbound  # noqa: E402


@pytest.fixture(autouse=True)
def reset_pfb_globals():
    _DNSMessage.instances = []

    pfb_unbound.pfb = {
        'mod_threading': True,
        'mod_ipaddress': True,
        'mod_maxminddb': False,
        'mod_sqlite3': True,
        'python_enable': False,
        'python_blacklist': False,
        'python_blocking': False,
        'python_reply': False,
        'python_nolog': False,
        'python_cname': False,
        'python_control': False,
        'python_hsts': False,
        'python_idn': False,
        'python_tld': False,
        'python_maxmind': False,
        'python_tld_seg': 2,
        'python_tlds': [],
        'dnsbl_ipv4': '10.10.10.1',
        'dnsbl_ipv6': '::1',
        'dataDB': False,
        'zoneDB': False,
        'regexDB': False,
        'whiteDB': False,
        'hstsDB': False,
        'gpListDB': False,
        'noAAAADB': False,
        'safeSearchDB': False,
        'sqlite3_dnsbl_con': False,
        'sqlite3_resolver_con': False,
        'rr_types': (1, 28, 255, 5, 39, 24, 15, 2, 12, 33, 16, 64, 65),
        'hsts_tlds': ('android', 'app', 'bank', 'chrome', 'dev', 'foo',
                      'gle', 'gmail', 'google', 'hangout', 'insurance',
                      'meet', 'new', 'page', 'play', 'search', 'youtube'),
        'pfb_py_dnsbl': ':memory:',
        'pfb_py_resolver': ':memory:',
        'pfb_py_cache': ':memory:',
    }
    pfb_unbound.dataDB = defaultdict(list)
    pfb_unbound.zoneDB = defaultdict(list)
    pfb_unbound.dnsblDB = defaultdict(list)
    pfb_unbound.safeSearchDB = defaultdict(list)
    pfb_unbound.feedGroupIndexDB = defaultdict(list)
    pfb_unbound.regexDB = defaultdict(str)
    pfb_unbound.whiteDB = defaultdict(str)
    pfb_unbound.hstsDB = defaultdict(str)
    pfb_unbound.gpListDB = defaultdict(str)
    pfb_unbound.noAAAADB = defaultdict(str)
    pfb_unbound.excludeDB = []
    pfb_unbound.excludeAAAADB = []
    pfb_unbound.excludeSS = []
    pfb_unbound.threads = []
