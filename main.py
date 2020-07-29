import collections
import sys
import re
import datetime
from dateutil.parser import parse
from pprint import pprint

class DefaultReader():
  @classmethod
  def _readline(cls, data):
    if type(data) is str:
      for entry in data.splitlines(True):
        yield entry
    elif isinstance(data, collections.Iterable):
      for entry in data:
        yield entry
    else:
      raise Exception(f"type {type(data)} is not supported")

  @classmethod
  def read(cls, data):
    for line in cls._readline(data):
      if line.strip() == "":
        continue
      yield line

class DefaultReader1():
  def __init__(self, data):
    self.data = data
  
  def __iter__(self):
    if type(self.data) is str:
      return iter(data.splitlines(True))
    elif isinstance(data, collections.Iterable):
      return iter(data)
    else:
      raise Exception(f"type {type(data)} is not supported")
    
class MultilineReader1():
  def __init__(self, data):
    self.data = data

  def set_start_marker(self, start_markter):
    self.start_marker = start_marker

  def __iter__(self):
    return self
  
  def __next__(self):
    pass
  
class MultilineReader(DefaultReader):
  start_marker = "^(\w\w\w +\d+ \d\d:\d\d:\d\d) ([^ ]+) (.+)\[(\d+)]: "
  
  @classmethod
  def set_start_marker(cls, start_markter):
    cls.start_marker = start_marker

  @classmethod
  def read(cls, data):
    # 最初にごみはない前提
    readiter = iter( cls._readline(data) )
    entry = next(readiter)
    for line in readiter:
      if re.search(cls.start_marker, line):
        yield entry
        entry = line
      else:
        entry += line
    yield entry

class DefaultTokenizer():
  @classmethod
  def tokenize(cls, string):
    return dict(message=string)

  def __init__(self, message):
    self.message = message

class SyslogTokenizer():
  today = datetime.datetime.now()
  thisyear = today.year
   
  @classmethod
  def tokenize(cls, string):
    if string.strip() == "":
      return dict()

    m = re.match("(\w\w\w +\d+ \d\d:\d\d:\d\d) ([^ ]+) (.+)\[(\d+)]: (.*)", string, re.MULTILINE + re.DOTALL)
    if m == None:
      return None

    dtstr = m.group(1)
    dt = parse(dtstr).replace(year=cls.thisyear)
    if cls.today < dt:
      dt = dt.replace(year=cls.thisyear-1)

    hostname = m.group(2)
    processname = m.group(3)
    processid = m.group(4)
    message = m.group(5)
    return dict(message=message, datetime=dt, hostname=hostname, processname=processname, processid=processid)

  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)

class DefaultObjectifier():
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
    if m := re.match('New session (?P<id>\d+) of user (?P<user>\w+).', tokens['message']):
      sessionid = int(m.group('id'))
      user = m.group('user')
      tokens['object'] = {
        'type': 'new',
        'id': sessionid,
        'user': user
      }
    elif m := re.match('Removed session (?P<id>\d+).', tokens['message']):
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

class LogParser():
    def __init__(self):
      self.reader = DefaultReader
      self.tokenizers = []
      self.objectifiers = []
      self.default_tokenizer = DefaultTokenizer
      self.default_objectifier = DefaultObjectifier

    def setReader(self, reader):
        self.reader = reader

    def addTokenizer(self, tokenizer):
      # プレフィックス部分を抽出する機能
      self.tokenizers.insert(0, tokenizer)

    def addObjectifier(self, objectifier):
      self.objectifiers.insert(0, objectifier)

    def _input(self, data):
      for line in self.inputter.read(data):
        yield line

    def _reader(self, data):
       return self.reader.read(data)

    def _tokenize(self, entry):
      for tokenizer in self.tokenizers:
        if result := tokenizer.tokenize(entry):
          return result
      else:
        return self.default_tokenizer.tokenize(entry)

    def _parse(self, tokens):
      for objectifier in self.objectifiers:
        if result := objectifier.parse(tokens):
          return result
      else:
        return self.default_objectifier.parse(tokens)

    def parse(self, entries):
      for entry in entries:
        tokens = self._tokenize(entry)
        obj = self._parse(tokens)
        yield obj

def main(data):
    parser = LogParser()
    #parser.setReader(DefaultReader)
    #parser.setReader(MultilineReader)
    parser.addTokenizer(SyslogTokenizer)
    parser.addObjectifier(SystemdLogind)
    reader = iter(DefaultReader().read(data))
    reader = iter(MultilineReader().read(data))
    it = parser.parse(reader)
    for entry in it:
      pprint(vars(entry))

if __name__ == "__main__":

    data = """
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
May 25 13:00:00 dev systemd-logind[1]: New session 2 of user user2.
May 25 13:10:00 dev systemd-logind[1]: New session 3 of user user3.
May 25 13:20:00 dev systemd-logind[1]: New session 4 of user user4.
May 25 13:20:00 dev systemd-logind[1]: New session 5 of user user5.
May 25 13:30:00 dev systemd-logind[1]: New session 5 of user user5a.
May 25 11:50:00 dev systemd-logind[1]: Removed session 0.
May 25 12:25:00 dev systemd-logind[1]: Removed session 0.
Jul 30 00:37:28 ubuntu NetworkManager[820]: <info>  [1593445048.6736] dhcp4 (ens33): option ip_address           => '192.168.61.131'
"""
    main(data)

