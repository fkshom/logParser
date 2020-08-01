
from pprint import pprint
from lib.logparser import LogParser
from lib.logparser.reader import DefaultReader, MultilineReader
from lib.logparser.tokenizer import SyslogTokenizer
from lib.logparser.objectifier import SystemdLogind

def validate_login_frequency(entries):
    """
    1分間に60回以上ログイン失敗がないかを調べる
    """
    pprint(vars(entries[5]))

def main(data):
    parser = LogParser()
    parser.addTokenizer(SyslogTokenizer)
    parser.addObjectifier(SystemdLogind)
    reader = iter(DefaultReader().read(data))
    reader = iter(MultilineReader().read(data))
    # it = parser.parse(reader)
    # for entry in it:
    #   pprint(vars(entry))

    entries = list(parser.parse(reader))

    validate_login_frequency(entries)
    # login and logout in 1minutes
    #[entry for entry in entries if entry['processname'] == 'systemd-logind']


if __name__ == "__main__":

    data = """\
Jun 30 00:22:28 ubuntu dbus-daemon[818]: [system] Successfully activated service 'org.freedesktop.nm_dispatcher'
Jun 30 00:22:39 ubuntu systemd[1]: NetworkManager-dispatcher.service: Succeeded.
Jun 30 00:25:58 ubuntu systemd-resolved[775]: Server returned error NXDOMAIN, mitigating potential DNS violation DVE-2018-0001, retrying transaction with reduced feature level UDP.
Jun 30 00:37:28 ubuntu NetworkManager[820]: <info>  [1593445048.6736] dhcp4 (ens33): option expiry               => '1593446848'
Jun 30 00:37:28 ubuntu dbus-daemon[818]: [system] Activating via systemd: service name='org.freedesktop.nm_dispatcher' unit='dbus-org.freedesktop.nm-dispatcher.service' requested by ':1.6' (uid=0 pid=820 comm="/usr/sbin/NetworkManager --no-daemon " label="unconfined")
May  5 12:00:00 dev systemd-logind[1]: New session 1 of user user1.
May 25 12:01:00 dev systemd-logind[1]: Removed session 1.
debug1
May 25 13:30:00 dev systemd-logind[1]: Removed session 2.
May 25 13:40:00 dev systemd-logind[1]: Removed session 3.
May 25 13:50:00 dev systemd-logind[1]: Removed session 4.
May 25 13:50:00 dev knockd[1]: 192.168.1.1: openSSH: Stage1
May 25 13:50:01 dev knockd[1]: 192.168.1.1: openSSH: Stage2
May 25 13:50:02 dev knockd[1]: 192.168.1.1: openSSH: OPEN SESAME
May 25 13:50:02 dev knockd[1]: openSSH: running command: /bin/iptables -I ...
May 25 13:50:05 dev knockd[1]: closeSSH: running command: /bin/iptables -D ...
May 25 13:00:00 dev systemd-logind[1]: New session 2 of user user2.
May 25 13:10:00 dev systemd-logind[1]: New session 3 of user user3.
May 25 13:20:00 dev systemd-logind[1]: New session 4 of user user4.
May 25 13:20:00 dev systemd-logind[1]: New session 5 of user user5.
May 25 13:30:00 dev systemd-logind[1]: New session 5 of user user5a.
May 25 11:50:00 dev systemd-logind[1]: Removed session 0.
May 25 12:25:00 dev systemd-logind[1]: Removed session 0.
Jul 30 00:37:28 ubuntu NetworkManager[820]: <info>  [1593445048.6736] dhcp4 (ens33): option ip_address           => '192.168.61.131'
"""  # noqa: E501
    main(data)
