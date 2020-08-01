from .reader import DefaultReader
from .tokenizer import DefaultTokenizer
from .objectifier import DefaultSyslogObject


class LogParser():
    def __init__(self):
      self.reader = DefaultReader
      self.tokenizers = []
      self.objectifiers = []
      self.default_tokenizer = DefaultTokenizer
      self.default_objectifier = DefaultSyslogObject

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
