import os
import sys

from abstract import Command
from tools import Table
from utils import fileutils
import utils


class DetectCommand(Command.Command):

    name = 'detect'
    usage = f'语法: {os.path.split(sys.argv[0])[1]} %s 文件名 文件路径...'
    description = '说明: 检测模式，检测词典文件的有效性'

    def __init__(self, args: list[str] = []):
        super().__init__(args)

    def argsHandle(self, args: list[str]):
        filesArgs = self._argsHandle(args)
        self.filesList = fileutils.getFilesList(filesArgs)
        config = {'sentence': True, 'mean-type': 0}
        self.wordsList, self.filesInfo = utils.readWordsFromFiles(self.filesList, config=config)

    def exec(self):
        super().exec()
        # print(self.filesInfo)
        # print(self.wordsList)
        print()
        table = Table.Table()
        table.titles = [
            ['ID', 0, Table.Table.ALIGN_RIGHT],
            '单词',
            '释义'
        ]
        for f in self.filesInfo.keys():
            print(f'[+] 文件“{f}”解析到了 {self.filesInfo.get(f, {}).get("total", 0)} 个单词。\n')
            for w in self.wordsList:
                # print(w.info.get('filepath'))
                if w.info.get('filepath') == f:
                    table.data.append([w.info.get('id', 0), w.word, w.mean])
            table.print()
            table.empty(True)
            print()
        print()
        print('='*192)
        self.printTitle('检测结果')
        total = 0
        for f in self.filesInfo.keys():
            print(f'    [+] 文件“{f}”解析到了 {self.filesInfo.get(f, {}).get("total", 0)} 个单词。')
            total += self.filesInfo.get(f, {}).get('total', 0)
        print(f'\n    [+] 总共解析到了 {total} 个单词。')
        print()
        self.printTitle('异常预览')
        noError = True
        for f in self.filesInfo.keys():
            error = self.filesInfo.get(f, {}).get('error', [])
            if len(error) != 0:
                noError = False
                for e in error:
                    print(f'    [-] {e}。')
        if noError:
            print('    [+] 暂无出现异常！')
