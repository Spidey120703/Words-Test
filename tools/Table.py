from typing import Union, List, Dict, AnyStr

from utils.stringutils import getDoubleWordsLen, getRealLen


class Table:
    """
    表格类，更多详情请见初始化方法
    """

    ALIGN_LEFT = 0
    """
    向左对齐
    """

    ALIGN_CENTER = 1
    """
    居中对齐
    """

    ALIGN_RIGHT = 2
    """
    向右对齐
    """

    data: List[List[AnyStr]] = []
    titles: List[Dict[AnyStr, Union[int, AnyStr]]] = []

    def __init__(self, data: List[List[AnyStr]] = None,
                 titles: List[Union[Dict[AnyStr, Union[int, AnyStr]], AnyStr]] = None):
        """
        表格类，
        主要用于在终端中绘制表格而封装的一个类，
        数据的大体格式是这样的：
        [
            ['第一行第一列', '第一行第二列', '第一行第三列'],
            ['第二行第一列', '第二行第二列', '第二行第三列'],
            ['第三行第一列', '第三行第二列', '第三行第三列'],
        ]
        标题的大体格式是这样的：
        [
            {
                'title': '标题',
                'width': 0,              # 默认宽度
                'align': ALIGN_LEFT      # 数据对齐方向，当前类的标志位
            },
            [
                '标题',
                0,
                ALIGN_LEFT
            ],
            '标题'
        ]

        :param data: 数据，可选
        :param titles: 标题，可选
        """
        if data is not None:
            self.data = data
        if data is not None:
            self.titles = titles

    def empty(self, onlyData: bool = False):
        self.data: List[List[AnyStr]] = []
        if not onlyData:
            self.titles: List[Dict[AnyStr, Union[int, AnyStr]]] = []

    def print(self, prefix: str = ' ', isShowTitle: bool = True):
        """
        绘制表格

        :param prefix: 表格前缀
        :param isShowTitle: 是否显示标题
        :return: 空
        """

        # 深拷贝，不修改源数据
        from copy import deepcopy
        titles = deepcopy(self.titles)
        data = deepcopy(self.data)
        totalCol = len(titles)
        for i, t in enumerate(titles):          # 检查标题数据结构，设置初始宽度
            if type(t) == str:                  # 判断是否为字符串
                titles[i] = {                   # 重新赋值
                    'title': t,                 # 将原来的字符串作为标题
                    'width': getRealLen(t)      # 设置初始宽度
                }
            elif type(t) in [dict, list]:               # 如果是字典
                if type(t) == list:
                    titles[i] = {
                        'title': str(titles[i][0]) if len(titles[i]) > 0 else '',
                        'width': int(titles[i][1]) if len(titles[i]) > 1 else 0,
                        'align': int(titles[i][2]) if len(titles[i]) > 2 else Table.ALIGN_LEFT
                    }
                titleRealLen = getRealLen(titles[i].get('title', ''))
                if titles[i].get('width', 0) < titleRealLen:
                    titles[i]['width'] = titleRealLen
            else:
                titles[i] = {
                    'title': str(t),
                    'width': getRealLen(str(t))
                }
        for i, _i in enumerate(data):
            for j, _j in enumerate(_i):
                if not isinstance(i, str):
                    data[i][j] = str(data[i][j])
        for i in data:
            curCol = len(i)
            if curCol > totalCol:
                titles += [{} for _ in range(curCol - totalCol)]
                totalCol = curCol
            for n, j in enumerate(i):
                curLen = getRealLen(j)
                titles[n]['width'] = curLen if curLen > titles[n].get('width', 0) \
                    else titles[n].get('width', 0)

        for n, i in enumerate(data):
            if len(i) < totalCol:
                data[n] += ['' for _ in range(totalCol - len(i))]

        def printSplitLine():
            """
            绘制表格分割线，一般情况下会输出在开头和结尾，还有标题与数据的交界处

            :return: 空
            """
            print(prefix + '+', end='')
            for _t in titles:
                print('-' * (_t.get('width', 0) + 2) + '+', end='')
            print()

        printSplitLine()
        if isShowTitle:
            print(prefix + '| ', end='')
            for t in titles:
                print(t.get('title', '').center(t.get('width', 0) - getDoubleWordsLen(t.get('title', ''))) + ' | ', end='')
            print()
            printSplitLine()
        for t in data:
            print(prefix + '| ', end='')
            for n, j in enumerate(t):
                print((
                      j.center(titles[n].get('width', 0) - getDoubleWordsLen(j)) if titles[n].get('align') == Table.ALIGN_CENTER else
                      j.rjust(titles[n].get('width', 0) - getDoubleWordsLen(j)) if titles[n].get('align') == Table.ALIGN_RIGHT else
                      j.ljust(titles[n].get('width', 0) - getDoubleWordsLen(j))) + ' | ', end='')
            print()
        printSplitLine()


if __name__ == '__main__':
    table = Table()
    table.titles = [
        {'title': '123', 'align': Table.ALIGN_RIGHT, 'width': -10},
        {'title': '456', 'align': Table.ALIGN_CENTER}, ['123', 23, 1]]
    table.data = [
        ['1', '22', '3'],
        ['11', '2'],
        ['12', '123123', '', '', '123'],
        ['啊']
    ]
    table.print()
    print(table.titles)
