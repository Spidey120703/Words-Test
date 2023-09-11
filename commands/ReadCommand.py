import os
import random
import time

from win32com import client as win32client

from abstract import Command
from tools import Speaker
from utils import coreutils, fileutils, stringutils
import utils


class ReadCommand(Command.Command):

    name = 'read'
    description = '说明: 阅读模式，阅读和浏览词汇'

    def __init__(self, args: list[str] = []):
        self.options.append(['begin', 'b', 'begin', '开始读的位置，序号，默认从头开始', int])
        voices = win32client.Dispatch("SAPI.SpVoice").GetVoices()
        self.options.append(['api', 'a', 'api', '语音接口，目前仅支持 3 种', int, (0, 2),
                             [
                                 ('值', '接口'),
                                 (0, 'Windows内置语音接口（无限制）（默认）'),
                                 (1, '有道接口（频繁请求可能会被封，请谨慎使用）'),
                                 (2, '百度接口（频繁请求可能会被封，请谨慎使用）')
                             ]])
        if voices.Count > 0:
            self.options.append(['rate', 'r', 'rate', '语音速度，仅在Windows内置语音中有效，有效值: [-10, 10]，默认为 3', int, (-10, 10)])
            self.options.append(['voice', 'v', 'voice', f'音色，仅在Windows内置语音中有效，有效值: [0, {voices.Count - 1}]，默认为 0', int, (0, voices.Count),
                                 [('值', '音色'), *enumerate([voices.Item(i).GetDescription() for i in range(voices.Count)])]])
        self.options.append(['lang', 'l', 'lang', '默认语言，仅在有道和百度中有效，目前仅支持两种', int, (0, 1), [
            ('值', '语言'),
            (0, '英文 - en_US（默认）'),
            (1, '中文 - zh_CN')
        ]])
        self.options.append(['domain', 'd', 'domain', '接口域名，选择切换有道接口，有道接口独有选项，有效值：[0, 1]，默认 0', int, (0, 1), [
            ('值', '接口'),
            (0, '有道语音接口'),
            (1, '有道词典接口')
        ]])
        self.options.append(['type', 't', 'type', '声音类型，有道接口独有选项，有效值：[0, 2]，默认为 0', int, (0, 2)])
        self.options.append(['speed', 's', 'speed', '声音速度，百度接口独有选项，有效值：[1, 7]，默认为 3', int, (1, 7)])
        self.options.append(['word', 'w', 'no-word', '不读单词'])
        self.options.append(['mean', 'm', 'no-mean', '不读意思'])
        self.options.append(['hide_word', 'hw', 'hide-word', '不显示单词'])
        self.options.append(['hide_mean', 'hm', 'hide-mean', '不显示意思'])
        self.options.append(['hide_other', 'ho', 'hide-other', '不显示其他扩展内容，听写时推荐加上此选项'])
        self.options.append(['random', 'R', 'random', '是否乱序，听写模式'])
        self.options.append(['phrase', 'P', 'phrase', '词组模式，不对释义进行解析，不对词组作太多解析'])
        self.options.append(['sentence', 'S', 'sentence', '句子模式，不对句子和释义进行解析'])
        self.options.append(['mean_type', 'T', 'mean-type', '释义解析格式，在词组模式中无效，在部分释义选项中有用，语音阅读的台词也基于这个来生成的', int, (0, 2),
                             [
                                 ('值', '意义'),
                                 (0, '不做解析'),
                                 (1, '星火，词性之间用双空格\'  \'，释义之间用序号标注\'①②③④⑤⑥⑦⑧⑨⑩\'（默认）'),
                                 (2, '其他，词性之间用空格\' \'，释义之间用全角分号\'；\'')
                             ]])
        self.options.append(['word_time', 'W', 'word-time', '单词阅读完后间隔的时间，默认停顿 2 秒', int])
        self.options.append(['mean_time', 'M', 'mean-time', '释义阅读完后间隔的时间，默认停顿 3 秒', int])
        self.options.append(['cache', 'c', 'cache', '缓存目录，默认当前目录', str, '路径'])
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
        print(f'[*] 已从 "{os.path.basename(self.filesList[0])}" {f"等 {len(self.filesList)} 个" if len(self.filesList) != 1 else ""}文件中读取了 {len(self.wordsList)} 个单词。')
        words = self.wordsList[self.args.get('begin', 0):]
        if len(words) == 0 or (self.args.get('word') and self.args.get('mean')):
            self.printError(f'错误: 没有单词需要读。', ['begin', 'word', 'mean'])
        if self.args.get('random'):
            random.shuffle(words)
        speaker = Speaker.Speaker()
        speaker.setApi(self.args.get('api', 0))
        speaker.cachePath = self.args.get('caches_dir', 'caches')
        speaker.setLang(self.args.get('lang', 0))
        speaker.setConfig({
            'voice': self.args.get('voice', 0),
            'rate': self.args.get('rate', 0),
            'domain': self.args.get('domain', 0),
            'type': self.args.get('type', 0),
            'speed': self.args.get('speed', 3)
        })
        try:
            print()
            for i, w in enumerate(words):
                print('-' * 81)
                print(f'({i + 1}/{len(words)})'.rjust(81))
                if not self.args.get('hide_word'):
                    print('单词:', w.word)
                    if len(w.parsedWord) != 1 and not self.args.get('phrase'):
                        print(' ' * 6 + w.variant)
                else:
                    print('单词:', coreutils.minCheck(w.word.__len__(), 8, 10) * '_')
                if not self.args.get('word'):
                    w.speakWord(speaker)
                print()
                time.sleep(self.args.get('word_time', 2))
                # print(w.mean)
                mean = list(w.parsedMean.items())
                posW = 0
                for p, _ in mean:
                    if isinstance(p, int):
                        continue
                    posW = len(p) if len(p) > posW else posW
                posW += 4
                print('释义: ')
                if not self.args.get('hide_mean'):
                    for p, l in mean:
                        if isinstance(p, int):
                            print(' ' * 6 + l)
                        else:
                            print(p.rjust(posW), end='')
                            isFirst = True
                            for tl in l:
                                if isFirst:
                                    isFirst = False
                                else:
                                    print(posW * ' ', end='')
                                print(tl)
                        print()
                else:
                    print(' ' * 6 + '_' * coreutils.minCheck(stringutils.getRealLen(w.mean), 8, 10))
                    print()
                if not self.args.get('mean'):
                    w.speakMean(speaker)
                if not self.args.get('hide_other'):
                    extended = w.info.get('extended')
                    if extended:
                        for e in extended.splitlines():
                            print(' ' * 2 + e)
                        print()
                if len(self.filesList) > 1 and w.info.get("filepath"):
                    print(f'* 来源于文件 "{os.path.basename(w.info.get("filepath"))}"。')
                print()
                time.sleep(self.args.get('mean_time', 2))
        except KeyboardInterrupt:
            print('\n' + '-' * 81 + '\n')
            print('[-] 您中断了程序。')
            print()
