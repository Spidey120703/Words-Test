import os
import random
import time

from win32com import client as win32client

from abstract import Command
from tools import SpeakerProcess, Speaker
from tools import Table, Timer
from utils import fileutils, stringutils
import utils


class TestCommand(Command.Command):

    name = 'test'
    description = '说明: 默写模式，默写单词或释义'

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
        self.options.append(['word', 'w', 'word', '默写单词（默认模式）'])
        self.options.append(['mean', 'm', 'mean', '默写意思，答对关键字即可'])
        self.options.append(['partial_mean', 'pM', 'partial-mean', '部分释义。词汇模式下，截取单个词性的意思进行抽默，词组模式下，以分号“；”截取释义。词数太多时不推荐，会有歧义。'])
        self.options.append(['phrase', 'P', 'phrase', '词组模式，不对释义进行解析，不对词组作太多解析'])
        self.options.append(['sentence', 'S', 'sentence', '句子模式，不对句子和释义进行解析'])
        self.options.append(['mean_type', 'M', 'mean-type', '释义解析格式，在词组模式中无效，在部分释义选项中有用，另外语音阅读的台词也基于这个来生成的', int, (0, 2),
                             [
                                 ('值', '意义'),
                                 (0, '不做解析'),
                                 (1, '星火，词性之间用双空格\'  \'，释义之间用序号标注\'①②③④⑤⑥⑦⑧⑨⑩\'（默认）'),
                                 (2, '其他，词性之间用空格\' \'，释义之间用全角分号\'；\'')
                             ]])
        self.options.append(['do_not_verbose', 'nV', 'do-not-verbose', '禁用输出输入的详细解析（如果输入的单词是另一个单词，直接输出该单词信息以便区分），和默写释义时输出的详细答案。'])
        self.options.append(['do_not_save', 'nS', 'do-not-save', '禁用错词本，默认情况下，当错误的单词超过 10 个时，会自动保存在当前目录'])
        self.options.append(['do_not_print', 'nP', 'do-not-print', '禁用错词输出，默认情况下，当错误的单词小于 24 个时，会直接输出在终端中'])
        self.options.append(['revise_dir', 'R', 'revise-dir', '复习目录，错误单词本保存的目录，默认为: ".\\revise"', str, '路径', r'^[^*?"<>|]+$'])
        self.options.append(['show_input', 'i', 'show-input', '是否在错词表格中显示当时输入的内容'])
        self.options.append(['prompt', 'p', 'prompt', '是否开启语音提示，只读英文'])
        self.options.append(['time', 'T', 'time', '停滞长达多久开启语音提示，单位秒，默认十秒，以下选项仅在开启语音提示后有效', int])
        voices = win32client.Dispatch("SAPI.SpVoice").GetVoices()
        self.options.append(['api', 'A', 'api', '语音接口，目前仅支持 3 种', int, (0, 2),
                             [
                                 ('值', '接口'),
                                 (0, 'Windows内置语音接口（无限制）（默认）'),
                                 (1, '有道接口（频繁请求可能会被封，请谨慎使用）'),
                                 (2, '百度接口（频繁请求可能会被封，请谨慎使用）')
                             ]])
        if voices.Count > 0:
            self.options.append(['rate', 'R', 'rate', '语音速度，仅在Windows内置语音中有效，有效值: [-10, 10]，默认为 3', int, (-10, 10)])
            self.options.append(['voice', 'v', 'voice', f'音色，仅在Windows内置语音中有效，有效值: [0, {voices.Count - 1}]，默认为 0', int, (0, voices.Count),
                                 [('值', '音色'), *enumerate([voices.Item(i).GetDescription() for i in range(voices.Count)])]])
        self.options.append(['domain', 'd', 'domain', '接口域名，选择切换有道接口，有道接口独有选项，有效值：[0, 1]，默认 0', int, (1, 2), [
            ('值', '接口'),
            (0, '有道语音接口'),
            (1, '有道词典接口')
        ]])
        self.options.append(['type', 't', 'type', '声音类型，有道接口独有选项，有效值：[0, 2]，默认为 0', int, (0, 2)])
        self.options.append(['speed', 's', 'speed', '声音速度，百度接口独有选项，有效值：[1, 7]，默认为 3', int, (1, 7)])
        self.options.append(['caches_dir', 'c', 'caches-dir', '音频缓存目录，默认当前目录下的cache文件夹', str, '路径'])
        super().__init__(args)

    def argsHandle(self, args: list[str]):
        filesArgs = self._argsHandle(args)
        self.filesList = fileutils.getFilesList(filesArgs)
        config = {}
        if self.args.get('sentence'):
            config['sentence'] = True
            config['mean-type'] = 0
        elif self.args.get('phrase'):
            config['phrase'] = True
            config['mean-type'] = 0
        else:
            config['mean-type'] = self.args.get('mean_type', 1)
        self.wordsList, self.filesInfo = utils.readWordsFromFiles(self.filesList, config=config)

    def exec(self):
        super().exec()
        print()
        print(f'[*] 已从 "{os.path.basename(self.filesList[0])}" {f"等 {len(self.filesList)} 个" if len(self.filesList) != 1 else ""}文件中读取了 {len(self.wordsList)} 个{"词组" if self.args.get("phrase") else "单词"}。')
        print()
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

        cur_test_type = '词组' if self.args.get('phrase') else '句子' if self.args.get('sentence') else '单词'

        incorrect = []
        table = Table.Table()
        table.titles = [
            cur_test_type, '释义'
        ]
        orderWidth = len(str(len(words)))
        if _range:
            orderWidth = len(start.__str__()) if len(start.__str__()) > orderWidth else orderWidth
        sepWidth = 0
        for w in words:
            sepWidth = stringutils.getRealLen(w.mean) if stringutils.getRealLen(w.mean) > sepWidth else sepWidth
        sepWidth += 10
        print("=" * sepWidth)
        if self.args.get('prompt'):
            speaker = Speaker.Speaker()
            speaker.setApi(self.args.get('api', 0))
            speaker.cachePath = self.args.get('caches_dir', 'caches')
            speaker.setConfig({
                'voice': self.args.get('voice', 0),
                'rate': self.args.get('rate', 0),
                'domain': self.args.get('domain', 0),
                'type': self.args.get('type', 0),
                'speed': self.args.get('speed', 3)
            })
            process = SpeakerProcess.SpeakerProcess(speaker, self.args.get('time', 10))
        timer = Timer.Timer()
        try:
            for i, w in enumerate(words):
                print(f'{(i + (start if _range and self.args.get("order") else 1)).__str__().rjust(orderWidth)}. ', end='')
                if self.args.get('word', True) and not self.args.get('mean'):
                    if self.args.get('partial_mean'):
                        if self.args.get('phrase'):
                            print(f'{random.choice(w.mean.split("；"))}')
                        else:
                            print(f'{random.choice(w.listedMean)}')
                    else:
                        print(f'{w.mean}')
                else:
                    print(f'{"词组" if self.args.get("phrase") else "句子" if self.args.get("sentence") else "词组" if " " in w.word else "单词"} "{w.word}" 的中文意思是 (   )')
                if self.args.get('prompt'):
                    if process.is_alive():
                        process.kill()
                    process = SpeakerProcess.SpeakerProcess(speaker, self.args.get('time', 10))
                    process.setWord(w)
                    process.start()
                ansIn = input('请输入: ').strip()\
                    .rstrip("'")\
                    .rstrip('"')\
                    .rstrip('\\')\
                    .rstrip('|')\
                    .rstrip(']')\
                    .rstrip('}')
                result = False
                if self.args.get('word', True) and not self.args.get('mean'):
                    if ansIn in w.parsedWord:
                        result = True
                else:
                    if len(ansIn) > 0 and ansIn in w.mean:
                        result = True
                if result:
                    print('回答正确 √')
                else:
                    print('回答错误 ×')
                    if self.args.get('word', True) and not self.args.get('mean'):
                        print(f'正确答案是{w.word}')
                        if not self.args.get('do_not_verbose', False):
                            for _w in words:
                                if ansIn in _w.parsedWord:
                                    print(f'\n您输入的 {ansIn} 意为')
                                    table.empty(True)
                                    table.data.append([_w.word, _w.mean])
                                    table.print('    ', False)
                    incorrect.append((w, ansIn))
                if self.args.get('mean'):
                    print(f'{cur_test_type} "{w.word}" 的中文释义是 "{w.mean}"。')
                    print()
                    if not self.args.get('do_not_verbose', False):
                        table.empty(True)
                        table.data.append([w.word, w.mean])
                        table.print(isShowTitle=False)
                        print()
                print()
        except KeyboardInterrupt:
            print('\n')
            print('[-] 您中断了程序。')
            print()
            i -= 1
        timer.stop()
        if self.args.get('prompt'):
            if process.is_alive():
                process.kill()
        print("=" * sepWidth)
        print()
        print(f'[*] 本次测试耗时%0.2f秒，共默写了{i + 1}个{cur_test_type}，其中正确的{cur_test_type}有{i - len(incorrect) + 1}个，错误的{cur_test_type}有{len(incorrect)}个，正确率为 %0.2f%%。' % (timer.spend, ((i - len(incorrect) + 1) / (i + 1) * 100) if i >= 0 else 0))

        if not self.args.get('do_not_print'):
            if 0 < len(incorrect) < 24:
                if self.args.get('show_input'):
                    if self.args.get('word', True) and not self.args.get('mean'):
                        table.titles = [
                            '输入', cur_test_type, '释义'
                        ]
                    else:
                        table.titles = [
                            cur_test_type, '释义', '输入'
                        ]
                table.empty(True)
                for w, i in incorrect:
                    if self.args.get('show_input'):
                        if self.args.get('word', True) and not self.args.get('mean'):
                            table.data.append([i, w.word, w.mean])
                        else:
                            table.data.append([w.word, w.mean, i])
                    else:
                        table.data.append([w.word, w.mean])
                self.printTitle(f'错{"误" if self.args.get("phrase") else "句" if self.args.get("sentence") else "词"}预览')
                table.print()

        if not self.args.get('do_not_save'):
            if len(incorrect) > 10:
                filename = f'{self.args.get("revise_dir", "revise")}/{time.strftime("%Y-%m-%d+%H_%M_%S")}.txt'
                fileutils.filePutContents(filename,
                                          '\r\n\r\n'.join([f'{i.word}\r\n{i.mean}' + (f'\r\n当时的答案\t{a}' if len(a) > 1 and self.args.get('show_input') else '') for i, a in incorrect]).encode())
                print(f'[*] 本次错{"误" if self.args.get("phrase") else "句" if self.args.get("sentence") else "词"}较多，已自动存入文件 "{filename}" 中了。')
