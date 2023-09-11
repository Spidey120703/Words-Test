import copy
import os
import random
import time

from abstract import Command
from tools import Table, Timer
from utils import fileutils, stringutils
import utils


class ChoiceCommand(Command.Command):
    name = 'choice'
    description = \
        '''说明: 选择模式，单词选择，给出单词或释义，从四个可选项中选出正确释义或单词。
      回答可通过: a、b、c、d 四个选项回答，不区分大小写，或者也可通过 1、2、3、4 回答。'''

    def __init__(self, args: list[str] = []):
        self.options.append(['order', 'o', 'order', '顺序模式，是否按照顺序默写，默认是乱序模式'])
        self.options.append(['amount', 'a', 'amount', '本次测试的单词数量，默认是无尽模式', int])
        self.options.append(['range', 'r', 'range', '默写的范围，序号不支持负数，支持格式有', str, '序号-序号', [
            ('传参', '说明'),
            ('2-12', '从第 2 个到第 12 个'),
            ('-10 ', '从第 1 个到第 10 个'),
            ('2-  ', '从第 2 个到最后一个'),
            ('10  ', '同 "-10"，从第 1 个到第 10 个')
        ], r'^\d*-?\d*$'])
        self.options.append(['strict', 's', 'strict', '严格模式，回车后直接判断对错，默认放松模式，可通过其他无效字符间接找到答案'])
        self.options.append(['word', 'w', 'word', '给出释义，选择单词'])
        self.options.append(['mean', 'm', 'mean', '给出单词，选择意思（默认模式）'])
        self.options.append(['partial_mean', 'pM', 'partial-mean', '部分释义。词汇模式下，截取单个词性的意思进行抽默，词组模式下，以分号“；”截取释义。词数太多时不推荐，会有歧义。'])
        self.options.append(['phrase', 'P', 'phrase', '词组模式，不对单词和释义进行解析'])
        self.options.append(['mean_type', 'M', 'mean-type', '释义解析格式，在词组模式中无效，在部分释义选项中有用，另外语音阅读的台词也基于这个来生成的', int, (0, 2),
                             [
                                 ('值', '意义'),
                                 (0, '不做解析'),
                                 (1, '星火，词性之间用双空格\'  \'，释义之间用序号标注\'①②③④⑤⑥⑦⑧⑨⑩\'（默认）'),
                                 (2, '其他，词性之间用空格\' \'，释义之间用全角分号\'；\'')
                             ]])
        self.options.append(['answer', 'A', 'answer', '回答结束后，详细输出每个选项所对应的单词和释义'])
        self.options.append(['do_not_save', 'S', 'do-not-save', '禁用错词本，默认情况下，当错误的单词超过 10 个时，会自动保存在当前目录'])
        self.options.append(['do_not_print', 'p', 'do-not-print', '禁用错词输出，默认情况下，当错误的单词小于 24 个时，会直接输出在终端中'])
        self.options.append(['revise_dir', 'R', 'revise-dir', '复习目录，错误单词本保存的目录，默认为: ".\\revise"', str, '路径', r'^[^*?"<>|]+$'])
        super().__init__(args)

    def argsHandle(self, args: list[str]):
        filesArgs = self._argsHandle(args)
        self.filesList = fileutils.getFilesList(filesArgs)
        config = {}
        if self.args.get('phrase'):
            config['phrase'] = True
            config['mean-type'] = 0
        else:
            config['mean-type'] = self.args.get('mean_type', 1)
        self.wordsList, self.filesInfo = utils.readWordsFromFiles(self.filesList, config=config)

    def exec(self):
        super().exec()
        print()
        print(f'[*] 已从 "{os.path.basename(self.filesList[0])}" {f"等 {len(self.filesList)} 个" if len(self.filesList) != 1 else ""}文件中读取了 {len(self.wordsList)} 个单词。')
        words = self.wordsList
        _range = self.args.get('range', False)
        if _range:
            if '-' not in _range:
                _range = '-' + _range
            start, end = _range.split('-')
            start = int(start) if len(start) > 0 else 1
            start = 1 if start < 1 else start
            end = int(end) if len(end) > 0 else len(words)
            if start > end:
                self.printError(
                    f'错误: 开始序号“{start}”大于结束序号“{end}”。',
                    'range'
                )
            if start == end:
                self.printError(
                    f'错误: 开始序号“{start}”等于结束序号“{end}”。',
                    'range'
                )
            words = words[start - 1:end]
        if not self.args.get('order', False):
            random.shuffle(words)
        amount = self.args.get('amount', False)
        if amount:
            words = words[:amount]

        incorrect = []
        table = Table.Table()
        table.titles = [
            '词组' if self.args.get('phrase') else '单词', '释义'
        ]
        if len(words) < 4:
            self.printError(f'错误: 有效单词数量只有 {len(words)} 个，当前功能最少需要 4 个及 4 个以上的单词')
        if self.args.get('word') and self.args.get('mean'):
            self.printError(f'错误: 不支持同时选择单词和释义', ['word', 'mean'])
        words = utils.wordsListToTupleList(words)
        orderWidth = len(str(len(words)))
        if _range:
            orderWidth = len(start.__str__()) if len(start.__str__()) > orderWidth else orderWidth
        sepWidth = 0
        for _, m, _ in words:
            sepWidth = stringutils.getRealLen(m) if stringutils.getRealLen(m) > sepWidth else sepWidth
        sepWidth += 10
        timer = Timer.Timer()
        print()
        try:
            for i, w in enumerate(words):
                while True:
                    options = []
                    otherWords = copy.deepcopy(words)
                    otherWords.remove(w)
                    ans = random.randint(0, 3)
                    for _ in range(4):
                        if _ == ans:
                            options.append(w)
                        else:
                            opt = random.choice(otherWords)
                            options.append(opt)
                            otherWords.remove(opt)
                    print("=" * sepWidth)
                    print(f'{(i + (start if _range and self.args.get("order") else 1)).__str__().rjust(orderWidth)}. ', end='')
                    if self.args.get('mean', True) and not self.args.get('word'):
                        print(f'{"词组" if " " in options[ans][0] else "单词"} "{options[ans][0]}" 的中文意思是 (   )')
                    else:
                        if self.args.get('partial_mean'):
                            if self.args.get('phrase'):
                                print(f'中文释义 "{random.choice(options[ans][1].split("；"))}" 的英文翻译是 (   )')
                            else:
                                print(f'中文释义 "{random.choice(options[ans][2][2])}" 的英文翻译是 (   )')
                        else:
                            print(f'中文释义 "{options[ans][1]}" 的英文翻译是 (   )')
                    print()
                    sing_opt = ''
                    for _i, o in enumerate(options):
                        print(f'    {chr(65 + _i)}. ', end='')
                        # print(o[1 if self.args.get('mean', True) and not self.args.get('word') else 0])
                        if self.args.get('mean', True) and not self.args.get('word'):
                            sing_opt = (random.choice(o[1].split("；")) if self.args.get('phrase') else random.choice(o[2][2])) if self.args.get('partial_mean') else o[1]
                        else:
                            sing_opt = o[0]
                        if _i == ans:
                            right_opt = sing_opt
                        print(sing_opt)
                    print()
                    ansIn = input('请做出你的选择: ').strip()
                    print()
                    result = False
                    if len(ansIn) == 1:
                        if ansIn.isalpha() and ord(ansIn.upper()) - 65 == ans:
                            result = True
                        elif ansIn.isnumeric() and int(ansIn) - 1 == ans:
                            result = True
                    if result:
                        print('[+] 恭喜你选对了！')
                    else:
                        if ansIn.upper() not in tuple('ABCD1234'):
                            print('[*] 选择无效。您的回答过于高级，本程序识别不了', end='')
                            if not self.args.get('strict'):
                                print('，要不再试试？')
                                print()
                                continue
                            else:
                                print('。')
                        else:
                            print(f'[-] 很遗憾你选错了。正确答案是 {chr(ans + 65)} 选项的 "{right_opt}"。')
                            print()
                            table.empty(True)
                            table.data.append(list(w[:2]))
                            table.print(isShowTitle=False)
                        incorrect.append(w[:2])
                    print()
                    if self.args.get('answer'):
                        table.empty(True)
                        for o in options:
                            table.data.append(list(o[:2]))
                        print()
                        print('所有选项的意思:')
                        print()
                        table.print()
                        print()
                    break
        except KeyboardInterrupt:
            print('\n')
            print('[-] 您中断了程序。')
            print()
            i -= 1
        timer.stop()
        print("=" * sepWidth)
        print()
        print(f'[*] 本次测试中，一共测试了 {i + 1} 道题，答对了 {i - len(incorrect) + 1} 题，答错了 {len(incorrect)} 题，正确率为 %0.2f%%，共用时 %s。' % (((i - len(incorrect) + 1) / (i + 1) * 100) if i >= 0 else 0, timer.strftime("%H 时 %M 分 %S 秒")))

        if not self.args.get('do_not_print'):
            if 0 < len(incorrect) < 24:
                table.empty(True)
                for w in incorrect:
                    table.data.append(list(w))
                self.printTitle('错词预览')
                table.print()

        if not self.args.get('do_not_save'):
            if len(incorrect) > 10:
                filename = f'{self.args.get("revise_dir", "revise")}/{time.strftime("%Y-%m-%d+%H_%M_%S")}.txt'
                fileutils.filePutContents(filename,
                                          '\r\n\r\n'.join(['\r\n'.join(i) for i in incorrect]).encode())
                print(f'[*] 本次错词较多，已自动存入文件 "{filename}" 中了。')

        # print(incorrect)
        # print(words)
