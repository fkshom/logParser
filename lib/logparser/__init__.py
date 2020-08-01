import collections
import re
import datetime
from dateutil.parser import parse


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
      return iter(self.data.splitlines(True))
    elif isinstance(self.data, collections.Iterable):
      return iter(self.data)
    else:
      raise Exception(f"type {type(self.data)} is not supported")


class MultilineReader1():
  def __init__(self, data):
    self.data = data

  def set_start_marker(self, start_marker):
    self.start_marker = start_marker

  def __iter__(self):
    return self

  def __next__(self):
    pass


class MultilineReader(DefaultReader):
  start_marker = r"^(\w\w\w +\d+ \d\d:\d\d:\d\d) ([^ ]+) (.+)\[(\d+)]: "

  @classmethod
  def set_start_marker(cls, start_marker):
    cls.start_marker = start_marker

  @classmethod
  def read(cls, data):
    # 最初にごみはない前提
    readiter = iter(cls._readline(data))
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

    m = re.match(r"(\w\w\w +\d+ \d\d:\d\d:\d\d) ([^ ]+) (.+)\[(\d+)]: (.*)", string, re.MULTILINE + re.DOTALL)
    if m is None:
      return None

    dtstr = m.group(1)
    dt = parse(dtstr).replace(year=cls.thisyear)
    if cls.today < dt:
      dt = dt.replace(year=cls.thisyear - 1)

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
