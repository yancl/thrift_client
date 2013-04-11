class TException(Exception):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return repr(self._value)

class ParamInvalidException(TException):
    def __init__(self, value):
        super(ParamInvalidException, self).__init__(value)
