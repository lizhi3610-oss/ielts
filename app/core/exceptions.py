class BusinessError(Exception):
    """
    业务异常。

    比如：题目不存在、回答内容为空。
    这类异常不是系统崩溃，而是用户请求不符合业务规则。
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
