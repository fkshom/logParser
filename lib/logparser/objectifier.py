import re


class DefaultSyslogObject():
  @classmethod
  def parse(cls, token):
    return cls(token)

  def __init__(self, token):
    self.__dict__.update(token)


class SystemdLogind():
  @classmethod
  def parse(cls, tokens):
    if type(tokens) is not dict:
      return None
    if tokens.get('processname') != 'systemd-logind':
      return None

    tokens['object'] = None
    if m := re.match(r'New session (?P<id>\d+) of user (?P<user>\w+).', tokens['message']):
      sessionid = int(m.group('id'))
      user = m.group('user')
      tokens['object'] = {
          'type': 'new',
          'id': sessionid,
          'user': user
      }
    elif m := re.match(r'Removed session (?P<id>\d+).', tokens['message']):
      sessionid = int(m.group('id'))
      tokens['object'] = {
          'type': 'del',
          'id': sessionid,
      }
    else:
      print('Unknown log entry type: ' + str(tokens))

    return cls(tokens)

  def __init__(self, token):
    self.__dict__.update(token)


class Knockd():
  @classmethod
  def parse(cls, tokens):
    """
    192.168.1.1: openSSH: Stage1
    192.168.1.1: openSSH: OPEN SESAME
    openSSH: running command: /bin/iptables -I ...
    192.168.1.1: closeSSH: Stage1
    192.168.1.1: closeSSH: OPEN SESAME
    closeSSH: running command: /bin/iptables -D ...
    """
    if type(tokens) is not dict:
      return None
    if tokens.get('processname') != 'knockd':
      return None
    tokens['object'] = None
    if m := re.match(r'\A(?P<ipaddr>[0-9]+.\.[0-9]+\.[0-9]+\.[0-9]+): (?P<type>open|close)SSH: Stage (?P<stage>\d+)\Z', tokens['message']):
      tokens['object'] = {
          'ipaddr': m.group('ipaddr'),
          'type': m.group('type'),
          'stage': m.group('stage'),
      }
    elif m := re.match(r'\A(?P<ipaddr>[0-9]+.\.[0-9]+\.[0-9]+\.[0-9]+): (?P<type>open|close)SSH: OPEN SESAME\Z', tokens['message']):
      tokens['object'] = {
          'ipaddr': m.group('ipaddr'),
          'type': m.group('type'),
      }
    elif m := re.match(r'\A(?P<type>open|close)SSH: running command: (?P<command>.+)\Z', tokens['message']):
      tokens['object'] = {
          'type': m.group('type'),
          'command': m.group('command'),
      }
    else:
      print('Unknown log entry type: ' + str(tokens))

    return cls(tokens)

  def __init__(self, token):
    self.__dict__.update(token)
