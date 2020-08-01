import datetime
import re
from dateutil.parser import parse


class DefaultTokenizer():
  @classmethod
  def tokenize(cls, string):
    return dict(raw=string)


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
    return dict(raw=string, datetime=dt, hostname=hostname, processname=processname, processid=processid, message=message)
