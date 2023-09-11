import re

from abstract import Command
from tools import Table
from utils import fileutils


class SearchCommand(Command.Command):

    name = 'search'
    description = '说明: 搜索模式，搜索单词或释义'

    def __init__(self, args: list[str] = []):
        self.options.append(['keyword', 'k', 'keyword', '预搜索关键字，逗号分割关键字，交互模式下失效', str, '关键字'])
        self.options.append(['regex', 'r', 'regex', '是否兼容正则表达式，推荐在交互模式中使用'])
        self.options.append(['word', 'w', 'word', '是否不匹配单词'])
        self.options.append(['mean', 'm', 'mean', '是否不匹配意思'])
        self.options.append(['path', 'p', 'path', '是否匹配路径'])
        self.options.append(['interact', 'i', 'interact', '是否开启交互模式'])
        self.options.append(['output', 'o', 'output', '重定向的文件，将搜索结果导出到文件中，不适用在交互模式', str, '文件名'])
        super().__init__(args)

    def exec(self):
        super().exec()
        if self.args.get('word') and self.args.get('mean'):
            self.printError('错误: 选项冲突。', ['word', 'mean'])
        table = Table.Table()
        table.titles = [
            '单词',
            '释义'
        ]
        try:
            # if not self.args.get('interact') and not self.args.get('keyword'):
            #     self.printError('错误: 搜索时需要关键字')
            while True:
                table.empty(True)
                if self.args.get('interact'):
                    print('\n' + '=' * 81)
                    keyword = input('[*] 请输入关键词: ')
                else:
                    keyword = self.args.get('keyword')
                if self.args.get('path'):
                    table.titles.append('路径')
                if self.args.get('regex'):
                    try:
                        for word in self.wordsList:
                            if not self.args.get('word'):
                                if re.search(keyword, word.word):
                                    table.data.append([word.word, word.mean])
                                    if self.args.get('path'):
                                        table.data[-1].append(word.info.get('filepath'))
                                    continue
                            if not self.args.get('mean'):
                                if re.search(keyword, word.mean):
                                    table.data.append([word.word, word.mean])
                                    if self.args.get('path'):
                                        table.data[-1].append(word.info.get('filepath'))
                                    continue
                            if self.args.get('path'):
                                if re.search(keyword, word.info.get('filepath')):
                                    table.data.append([word.word, word.mean, word.info.get('filepath')])
                                    continue
                    except re.error:
                        pass
                else:
                    if keyword:
                        keywords = keyword.split(',')
                    else:
                        keywords = ['']
                    for word in self.wordsList:
                        for kw in keywords:
                            if not self.args.get('word'):
                                if kw in word.word:
                                    table.data.append([word.word, word.mean])
                                    if self.args.get('path'):
                                        table.data[-1].append(word.info.get('filepath'))
                                    break
                            if not self.args.get('mean'):
                                if kw in word.mean:
                                    table.data.append([word.word, word.mean])
                                    if self.args.get('path'):
                                        table.data[-1].append(word.info.get('filepath'))
                                    break
                            if self.args.get('path'):
                                if kw in word.info.get('filepath'):
                                    table.data.append([word.word, word.mean, word.info.get('filepath')])
                                    break
                if len(table.data) > 0:
                    self.printTitle('搜索结果')
                    table.print()
                    print()
                    print(f'[*] 关键词 "{keyword if keyword else ""}" 搜索到了 {len(table.data)} 条结果。')
                else:
                    print()
                    print(f'[-] 没有搜索到任何关于关键词 "{keyword}" 的结果。')
                if not self.args.get('interact'):
                    if self.args.get('output'):
                        save = self.args.get('output')
                        # print(table.data)
                        fileutils.filePutContents(save, '\r\n\r\n'.join(['\r\n'.join(w[:2]) for w in table.data if len(w) > 1]).encode())
                        print(f'[+] 已将 {len(table.data)} 条结果写入到文件 "{save}" 中。')
                    break
        except KeyboardInterrupt:
            print('\n' + '=' * 81 + '\n')
            print('[-] 您中断了程序。')
            print()
