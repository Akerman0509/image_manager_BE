


class APIWarningException(Exception):
    def __init__(self, message='', error='', http_status=200):
        self.error = error
        self.http_status = http_status
        super(APIWarningException, self).__init__(message)