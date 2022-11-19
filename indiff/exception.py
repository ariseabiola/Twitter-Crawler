class ZeroTweetError(Exception):

    def __init__(self, message):
        self.message = message


class WebBrowserError(Exception):

    def __init__(self, message):
        self.message = message


class WebDriverError(Exception):

    def __init__(self, message):
        self.message = message
