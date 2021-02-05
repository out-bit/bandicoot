class DecryptException(Exception):
    pass

class DecryptWrongKeyException(DecryptException):
    pass

class DecryptNotClearTextException(DecryptException):
    pass
