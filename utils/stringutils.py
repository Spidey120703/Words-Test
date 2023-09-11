def getDoubleWordsLen(s: str):
    """
    获取双字宽字符的数量，输出时需要，修复了好久的bug

    :param s: 字符串
    :return: 数量
    """
    l = 0
    for __i in s:
        if len(__i.encode('gbk')) != 1:
            l += 1
    return l


def getRealLen(s: str):
    """
    获得当前字符串的真实长度，或者说是终端中，字符的真实占宽，
    一般情况下，像中文字符之类的unicode扩展字符在终端中占用两个字符空间

    :param s: 输入的字符串
    :return: 真实长度
    """
    return len(s.encode('gbk'))


def ljust(__str: str, __width: int = 0):
    return __str.ljust(__width - getDoubleWordsLen(__str))


def rjust(__str: str, __width: int = 0):
    return __str.rjust(__width - getDoubleWordsLen(__str))
