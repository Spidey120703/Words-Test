import os
import re
import sys

from utils import coreutils, fileutils
from utils import utils

from typing import Union


class Command:
    name = 'command'
    usage = f'语法: {os.path.split(sys.argv[0])[1]} %s -选项:值 --选项=值 文件名 文件路径...'
    description = '说明: 暂无说明'
    args = {}
    filesList = []
    wordsList = []
    filesInfo = {}
    options = [
        ['help', ('h', 'H'), 'help', '显示帮助信息'],
        # ['test', 't', 'test', '测试选项', int, (-10, 10)],
        # ['demo', 'd', None, '演示选项']
    ]
    # ['选项变量名', '-选项', '--选项', '选项描述', 类型, ...拓展参数]
    # ['选项变量名', '-选项', '--选项', '选项描述', int, (起始有效值, 结束有效值), [
    #   ('值标题', '意义标题'),
    #   ('值', '意义'), ...
    # ]]
    # ['选项变量名', '-选项', '--选项', '选项描述', str, '值说明', '正则表达式']
    # ['选项变量名', '-选项', '--选项', '选项描述', str, '值说明', [
    #   ('值标题', '意义标题'),
    #   ('值', '意义'), ...
    # ]]

    def __init__(self, args: list[str] = []):
        try:
            if len(args) == 0:
                utils.printHelp([self.usage % self.name,
                                 self.description,
                                 ' * 详细信息请查看命令帮助 "-h" 或 "--help"'])
                exit(1)
            self.argsHandle(args)
        except Exception as e:
            if len(e.args) == 1:
                utils.printHelp(['错误: ' + e.__str__(),
                                 ('选项', self.help())])
            else:
                utils.printHelp(['错误: ' + e.args[0],
                                 ('选项', [self.help()[e.args[1]]])])
        # print(self.help())

    def exec(self):
        if self.args.get('help', False):
            utils.printHelp([self.usage % self.name,
                                 self.description,
                             ('选项', self.help())])
        else:
            if len(self.filesList) == 0:
                utils.printHelp(['错误: 目前没有找到有效词典文件，请选择词典文件', self.usage % self.name])
            if len(self.wordsList) == 0:
                utils.printHelp(['错误: 目前没有读取到有效的单词，请选择有效的词典文件', self.usage % self.name])

    def optionParse(self, opt: str):
        result = {}
        for _n, o in enumerate(self.options):
            for l, a in [*enumerate(o)][1:3]:
                if o[l] is None:
                    continue
                if not isinstance(o[l], tuple):
                    o[l] = (o[l],)
                for so in o[l]:
                    haveArgument = len(o) > 4
                    if haveArgument:
                        if opt.startswith('-' * l + so + (':' if l == 1 else '=')):
                            temp = opt[len(so) + l + 1:]
                            try:
                                temp = int(temp) if o[4] == int else \
                                    float(temp) if o[4] == float else \
                                    bool(temp) if o[4] == bool else temp
                            except ValueError:
                                raise Exception(f'选项 "{opt}" 中的参数 "{temp}" 不是一个有效的数字', _n)
                            if o[4] == int:
                                if (coreutils.inRange(temp, o[5]) if isinstance(o[5], tuple) else True) if \
                                        len(o) > 5 else True:
                                    result[o[0]] = temp
                                else:
                                    raise Exception(f'选项 "{opt}" 中的参数 "{temp}" 不在 {o[5][0]} 和 {o[5][1]} 范围内', _n)
                            elif o[4] == str:
                                if len(o) > 7 and isinstance(o[7], str):
                                    if re.match(o[7], temp):
                                        result[o[0]] = temp
                                else:
                                    result[o[0]] = temp
                        elif opt == ('-' * l + so):
                            raise Exception(f'选项 "{opt}" 需要参数', _n)
                    else:
                        if opt == ('-' * l + so):
                            result[o[0]] = True
                        elif opt.startswith('-' * l + so + (':' if l == 1 else '=')):
                            raise Exception(f'选项 "{opt.split(":")[0].split("=")[0]}" 不需要参数', _n)
        if len(result) == 0:
            raise Exception(f'选项 "{opt}" 无效')
        return result

    def _argsHandle(self, args: list[str]) -> list:
        filesArgs = []
        for a in args:
            if a.startswith('-'):
                self.args.update(self.optionParse(a))
            else:
                filesArgs.append(a)
        return filesArgs

    def argsHandle(self, args: list[str]):
        filesArgs = self._argsHandle(args)
        # print(self.args)
        self.filesList = fileutils.getFilesList(filesArgs)
        self.wordsList, self.filesInfo = utils.readWordsFromFiles(self.filesList)

    def printError(self, errorMsg: str, opt: Union[list[str], str] = None, *args):
        return utils.printHelp([
            errorMsg,
            ('选项', self.getOptionHelp(opt)) if opt is not None else None,
            *args
        ])

    def getOptionHelp(self, opt: Union[list[str], str]):
        if isinstance(opt, str):
            opt = [opt]
        opts = []
        for o in self.options:
            if o[0] in opt:
                opts.append(self.helpImpl(o))
        return opts

    @staticmethod
    def helpImpl(o):
        tmpStr = ''
        for l, a in [*enumerate(o)][1:3]:
            if o[l] is None:
                continue
            if not isinstance(o[l], tuple):
                o[l] = (o[l],)
            for so in o[l]:
                tmpStr += '-' * l + so
                if len(o) > 4:
                    tmpStr += ':' if l == 1 else '='
                    # if len(o) > 5:
                    #     tmpStr += f'[{o[5][0]}:{o[5][1]}]'
                    # else:
                    #     tmpStr += '<' + ('整数' if o[4] == int else
                    #                      '小数' if o[4] == float else
                    #                      '布尔值' if o[4] == bool else '字符串') + '>'
                    # 太术语化了，太专业了
                    # tmpStr += ('整数' if o[4] == int else
                    #            '小数' if o[4] == float else
                    #            '布尔值' if o[4] == bool else '字符串')
                    tmpStr += ('整数' if o[4] == int else
                               '小数' if o[4] == float else
                               'true/false' if o[4] == bool else (
                                   o[5] if len(o) > 5 and isinstance(o[5], str) else '字符串'))
                tmpStr += ', '
        if len(o) > 6 and isinstance(o[6], list):
            # print(o[6])
            return tmpStr[:-2], (o[3], o[6])
        else:
            return tmpStr[:-2], o[3]

    def help(self):
        optStr = []
        for o in self.options:
            optStr.append(self.helpImpl(o))
        return optStr

    @staticmethod
    def printTitle(title: str):
        print(f'\n ###[ {title} ]###\n')

    # def help(self):
    #     optStr = []
    #     optStrWidth = 0
    #     for o in self.options:
    #         tmpStr = '    '
    #         for l, a in [*enumerate(o)][1:3]:
    #             if o[l] is None:
    #                 continue
    #             if not isinstance(o[l], tuple):
    #                 o[l] = (o[l],)
    #             for so in o[l]:
    #                 tmpStr += '-' * l + so
    #                 if len(o) > 4:
    #                     tmpStr += ':' if l == 1 else '='
    #                     tmpStr += '<' + ('整数' if o[4] == int else
    #                                      '小数' if o[4] == float else
    #                                      '布尔值' if o[4] == bool else '字符串') + '>'
    #                 tmpStr += ', '
    #         optStr.append(tmpStr[:-2])
    #         tmpWidth = stringutils.getRealLen(tmpStr)
    #         optStrWidth = tmpWidth if tmpWidth > optStrWidth else optStrWidth
    #     optStrWidth += 2
    #     print('选项：')
    #     for i, t in enumerate(optStr):
    #         print(t.ljust(optStrWidth - stringutils.getDoubleWordsLen(t)), end='')
    #         print(self.options[i][3])
