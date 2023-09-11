import os.path
import re

from abstract import Command
from tools import Table
from utils import fileutils
import utils


class ConvertCommand(Command.Command):
    name = 'convert'
    description = '说明: 词典转换模式，务必检查文件内容，当前不支持自动识别功能，另外文件名不要重名，会被覆盖写入'

    def __init__(self, args: list[str] = []):
        self.options.append(['single-line-with-space', 'sS', 'single-space', '单词与释义空格间隔，每个单词作一行，支持词组，例如：word 释义'])
        self.options.append(['single-line-with-tab', 'sT', 'single-tab', '单词与释义制表符间隔，每个单词作一行，        例如：word    释义'])
        self.options.append(
            ['single-line-with-comma', 'sC', 'single-comma', '单词与释义逗号间隔，每个单词作一行，          例如：word,释义'])
        # self.options.append(
        #     ['single-line-with-comma', 'sC', 'single-comma', '单词与释义逗号间隔，每个单词作一行，类似于CSV(Comma-Separated Values)逗号分隔值'])
        # self.options.append(['double-line-with-break', 'sB', 'double-break',
        #                      '单词与释义换行间隔，每个单词作两行，有别于当前程序标准格式，标准格式是每个单词占用3行，一行词汇行，一行释义行，一行空白行'])
        self.options.append(['double-line-with-break', 'dB', 'double-break',
                             '单词与释义换行间隔，每个单词作两行，          例如：word\\n释义'])
        self.options.append(['decode', 'd', 'decode', '编码转换，可自行指定编码格式，例如：ansi、utf-8等', str, '编码'])
        self.options.append(['reverse', 'r', 'reverse', '是否为逆向转换，默认是将未知格式内容转化成标准格式内容'])
        self.options.append(['word', 'w', 'word', '是否只导出英文'])
        self.options.append(['mean', 'm', 'mean', '是否只导出释义'])
        self.options.append(['output-path', 'o', 'output-path', '文件导出路径，默认为当前目录下的 output 文件夹下', str, '路径'])
        super().__init__(args)

    @staticmethod
    def findSpaceSep(__str: str, __startIndex: int = 0):
        __index = __str.find(' ', __startIndex)
        __index2 = __str.find(' ', __index + 1)
        if __index2 == -1 or re.search(r'[^A-Za-z/\-()]', __str[__index + 1: __index2]):
            return __index
        else:
            return ConvertCommand.findSpaceSep(__str, __index2 + 1)

    @staticmethod
    def spaceSplit(__content: str):
        __sep = ConvertCommand.findSpaceSep(__content)
        return __content[:__sep], __content[__sep + 1:]

    def argsHandle(self, args: list[str]):
        filesArgs = self._argsHandle(args)
        self.filesList = fileutils.getFilesList(filesArgs)

    def exec(self):
        if self.args.get('help', False):
            utils.printHelp([self.usage % self.name,
                                 self.description,
                             ('选项', self.help())])
        bool2int = lambda b: 1 if b else 0
        if bool2int(self.args.get('single-line-with-space')) + bool2int(self.args.get('single-line-with-tab')) + bool2int(self.args.get('single-line-with-comma')) + bool2int(self.args.get('double-line-with-break')) > 1:
            self.printError('错误: 选项中有冲突', ['single-line-with-space', 'single-line-with-tab', 'single-line-with-comma', 'double-line-with-break'])
        if bool2int(self.args.get('word')) + bool2int(self.args.get('mean')) > 1:
            self.printError('错误: 选项中有冲突', ['word', 'mean'])
        try:
            fileList = {}
            for file in self.filesList:
                with open(file, 'rb+') as rf:
                    fileList[file] = []
                    if self.args.get('single-line-with-space') or self.args.get('single-line-with-tab') or self.args.get('single-line-with-comma') or self.args.get('double-line-with-break'):
                        for l in rf.readlines():
                            l = l.strip().decode(self.args.get('decode'))
                            if self.args.get('single-line-with-space'):
                                fileList[file].append(self.spaceSplit(l))
                            elif self.args.get('single-line-with-tab'):
                                fileList[file].append(l.split('\t', 1))
                            elif self.args.get('single-line-with-comma'):
                                fileList[file].append(l.split(',', 1))
                            elif self.args.get('double-line-with-break'):
                                if re.match(r'^[A-Za-z/\- ()]+?$', l):
                                    fileList[file].append([l])
                                else:
                                    fileList[file][len(fileList[file]) - 1].append(l)
                    for i in rf.read().decode(self.args.get('decode')).split('\r\n\r\n'):
                        fileList[file].append(i.split('\r\n')[:2])
            table = Table.Table()
            table.titles.append(['序号', 0, Table.Table.ALIGN_CENTER])
            table.titles.append('词汇')
            table.titles.append('释义')
            for file in fileList:
                save = os.path.join(self.args.get('output-path', 'output'), os.path.basename(file))
                table.empty(True)
                for i, w in enumerate(fileList[file]):
                    if len(w) > 1:
                        table.data.append([i+1, *w[:2]])
                print(f'[+] 文件 "{file}" ({len(table.data)}词)')
                if len(table.data) > 0:
                    table.print()
                    if self.args.get('word'):
                        fileutils.filePutContents(save, '\r\n'.join([w[0] for w in fileList[file] if len(w) > 1]).encode())
                    elif self.args.get('mean'):
                        fileutils.filePutContents(save, '\r\n'.join([w[1] for w in fileList[file] if len(w) > 1]).encode())
                    else:
                        fileutils.filePutContents(save, '\r\n\r\n'.join(['\r\n'.join(w[:2]) for w in fileList[file] if len(w) > 1]).encode())
                    print(f'[+] 成功{f"地只将" + ("释义" if self.args.get("mean") else "单词") if self.args.get("word") or self.args.get("mean") else ""}导出到了 "{save}" 中。')
                else:
                    print(f'[-] 暂未在 "{file}" 扫描到任何有效单词。')
                print()
        except KeyboardInterrupt:
            self.printError('错误: 转换过程中被中断，可能会造成部分数据丢失...')
        except:
            self.printError('错误: 文件解析过程中出现错误...')

