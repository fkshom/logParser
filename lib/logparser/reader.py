import collections
import re


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
