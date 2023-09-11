import os.path
import sys
from typing import *
from collections import OrderedDict
import re

from tools import Table, Speaker
from abstract import Word
from utils import stringutils


def parseWord(word: AnyStr):
    """
    解析单词，分解成多个备选答案

    :param word: 单词
    :return: 单词列表
    """
    return list({*parseWordImpl(word), word})


def parseWordImpl(words: Union[str, List[str]]):
    """
    解析单词的实现方法，核心代码

    :param words: 单词或单词列表
    :return: 单词列表
    """
    parsedWord = []
    if type(words) != list:
        words = [words]
    for word in words:
        if '(' in word and ')' in word:
            parsedWord.append(
                word.replace('(', '', 1)
                    .replace(')', '', 1))
            parsedWord.append(
                word[:word.index('(')] +
                word[word.index(')') + 1:])
            parsedWord = parseWordImpl(parsedWord)
        # elif '/-' in word:
        #     parsedWord.append(word[:word.index('/-')])
        #     parsedWord.append(word[:word.index('/-') - len(word[word.index('/-') + 2:])] +
        #                       word[word.index('/-') + 2:])
        elif '/' in word:
            # parsedWord.extend()
            res = []
            for i in word.split('/'):
                if len(res) == 0 or i[0] != '-':
                    res.append(i)
                else:
                    res[-1] += '/' + i
            # print(res)
            for i in res:
                if '/-' in i:
                    # parsedWord.append(i[:i.index('/-')])
                    # parsedWord.append(i[:i.index('/-') - len(i[i.index('/-') + 2:])] +
                    #                   i[i.index('/-') + 2:])
                    prefix, suffix = i.rsplit('/-', 1)
                    parsedWord.append(prefix)
                    parsedWord.append(prefix[:-len(suffix)] + suffix)
                else:
                    parsedWord.append(i)
            # parsedWord.extend(res)
        else:
            parsedWord.append(word)
    parsedWord = list(set(parsedWord))
    return parsedWord


def parseMean(mean: AnyStr, type: int = 1):
    """
    解析意思，解析翻译

    :param mean: 翻译字符串
    :return: 解析后的可排序字典
    """
    if type == 1:
        return _parseMeanXingHuo(mean)
    else:
        return _parseMeanOther(mean)


def simplifySpace(string: str):
    while '  ' in string:
        string = string.replace('  ', ' ')
    return string


def _parseMeanOther(mean: AnyStr):
    _mean = simplifySpace(mean.strip()) + ' '
    parsedMean = OrderedDict()
    posIter = []  # Part of Speech
    while _mean.__contains__(' '):
        _part, _mean = _mean.split(' ', 1)
        if not re.match(r'^[a-z]*(?:[a-z.]|[.]/)*[a-z]+?[.]', _part):
            if len(posIter) > 0:
                posIter[-1] += ' ' + _part
                continue
        if len(_part) > 0:
            posIter.append(_part)
    for t in posIter:
        tt = t.split('；')
        posMatch = re.search(r'^[a-z]*(?:[a-z.]|[.]/)*[a-z]+?[.]', t)
        if posMatch:
            offset = posMatch.span()[1]
            parsedMean[t[:offset]] = [tt[0][offset:], *tt[1:]]
        else:
            parsedMean[len(parsedMean)] = t
    return parsedMean, posIter


def _parseMeanXingHuo(mean: AnyStr):
    parsedMean = OrderedDict()
    posIter = mean.split('  ')  # Part of Speech
    # print(pos)
    for t in posIter:
        tt = []
        for i in t.strip().split(' '):
            if len(tt) == 0 or i[0] in "①②③④⑤⑥⑦⑧⑨⑩":
                tt.append(i)
            else:
                tt[-1] += ' ' + i
        # print(tt)
        posMatch = re.search(r'^[a-zA-Z\-/.,() ]+', t)
        if posMatch:
            offset = posMatch.span()[1]
            offset -= 1 if t[offset - 1] == '(' else 0  # 以防误删括号
            parsedMean[t[:offset]] = [tt[0][offset:], *tt[1:]]
        else:
            parsedMean[len(parsedMean)] = t
    # print(parsedMean)
    return parsedMean, posIter


abbrDict = {
    # 词性符合和略语
    'n.': '名词', 'v.': '动词',
    'vt.': '及物动词', 'vi.': '不及物动词',
    'a.': '形容词', 'ad.': '副词',
    'pron.': '代词', 'prep.': '介词',
    'conj.': '连词', 'int.': '感叹词',
    'link.v.': '连系动词', 'sb.': '(=somebody)某人',
    'sth.': '(=something)某物', '(BrE)': '英式英语',
    '(AmE)': '美式英语',
    # 语法符号
    '(sing.)': '名词的单数形式', '(常 sing.)': '常用单数',
    '(pl.)': '名词的复数形式', '(常 pl.)': '常用复数'
}

translateDict = {
    # 词性符合和略语
    'n.': '名词', 'v.': '动词',
    'vt.': '及物动词', 'vi.': '不及物动词',
    'a.': '形容词', 'ad.': '副词',
    'pron.': '代词', 'prep.': '介词',
    'conj.': '连词', 'int.': '感叹词',
    'link.v.': '连系动词', 'sb.': 'somebody',
    'sth.': 'something', '(BrE)': '英式英语，译为',
    '(AmE)': '美式英语，译为',
    '(sing.)': '名词的单数形式，译为', '(常 sing.)': '常用单数，译为',
    '(pl.)': '名词的复数形式，译为', '(常 pl.)': '常用复数，译为'
}


def getDialogue(parsedMean: OrderedDict, word: AnyStr = '当前单词', part: int = 0):
    """
    生成人性化描述台词

    :param parsedMean: 解析后的意思，类型为可排序型字典
    :param word: 单词，部分翻译中会有其替代符号
    :param part: 部分
    :return: 台词
    """
    # print(parsedMean)
    dialogue = ''
    for p, m in parsedMean.items():
        if type(p) == str:
            p = getDialogueImpl(p, word, 0)
            p += '，可译为'
            # print(p)
            dialogue += p
            dialogue += '：' + '；'.join([getDialogueImpl(im[1:] if len(m) > 1 else im, word, 1) for im in m]) + '。'
            # dialogue += '：' + '；'.join([getDialogueImpl(im[1:], word) for im in m] if len(m) > 1 else m) + '。'
        else:
            dialogue += m.replace('…', '什么') + '。'
    return dialogue


def getDialogueImpl(mean: AnyStr, word: AnyStr, part: int = 0):
    """
    生成人性化描述台词的实现方法，翻译部分的核心代码

    :param mean: 意思
    :param word: 单词
    :param part: 部分
    :return:
    """
    for a in translateDict.items():
        mean = mean.replace(a[0], a[1])
    mean = mean.replace('/', '或')
    mean = mean.replace('(pl. ', '，(复数形式为')
    mean = mean.replace('~', word)
    mean = mean.replace(' -', ' ' + word)
    collocationMatch = re.search(r'\([a-z,]+\)', mean)
    while collocationMatch:
        offset = collocationMatch.span()
        mean = mean[:offset[0]] + '，与' + mean[offset[0] + 1: offset[1] - 1].replace(',', '和') + '搭配' + mean[offset[1]:]
        collocationMatch = re.search(r'\([a-z,]+\)', mean)
    nounsMatch = re.search(r'\([A-Z]-\)', mean)
    while nounsMatch:
        offset = nounsMatch.span()
        # mean = mean[:offset[0]] + '(' + word[0].upper() + word[1:] + '首字母大写' + ')，' + mean[offset[1]:]
        mean = mean[:offset[0]] + ('，' if part == 0 else '') + '(当' + word[0].upper() + word[1:] + '首字母大写时)' + \
               ('，译为' if part == 1 else '') + mean[offset[1]:]
        nounsMatch = re.search(r'\([A-Z]-\)', mean)
    if re.search(r'\([a-zA-Z ]?-[es]{1,2}\)', mean):
        # print(1)
        mean = mean.replace('-', word)
    mean = mean.replace('…', '什么')
    # pluralMatch = re.search(r'\([A-Z]-\)', mean)
    # while nounsMatch:
    #     offset = nounsMatch.span()
    #     # mean = mean[:offset[0]] + '(' + word[0].upper() + word[1:] + '首字母大写' + ')，' + mean[offset[1]:]
    #     mean = mean[:offset[0]] + '(当' + word[0].upper() + word[1:] + '首字母大写)' + mean[offset[1]:]
    #     pluralMatch = re.search(r'\([A-Z]-\)', mean)
    # mean = mean.replace('……', '什么什么')
    return mean


def readWordsFromFiles(filesList, sep: tuple[bytes, bytes] = (b'\r\n\r\n', b'\r\n'), config: dict = {}) -> (
        Word.Word, dict):
    wordsList = []
    filesInfo = {}
    for fn in filesList:
        with open(fn, 'rb+') as f:
            filesInfo[fn] = {
                'total': 0,
                'error': []
            }
            for i, l in enumerate(f.read().split(sep[0])):
                l = l.strip()
                if l != b'':
                    i += 1
                    # wordsList.append(Word.Word(*[t.decode() for t in l.split(sep[1])[:2]], {'filepath': fn, 'id': i}))
                    splited = l.split(sep[1])
                    if len(splited) < 2:
                        print()
                        print(f'[-] 解析文件 "{os.path.basename(fn)}" 的第 {i} 个单词时出现了格式错误')
                        filesInfo[fn]['error'].append(f'解析文件 "{fn}" 的第 {i} 个单词时出现了格式错误')
                        i -= 1
                        continue
                    try:
                        wordsList.append(Word.Word(*[t.decode() for t in splited[:2]], {'filepath': fn, 'id': i, 'extended': b'\n'.join(splited[2:]).decode() if len(splited) > 2 else None, **config}))
                    except UnicodeDecodeError:
                        print()
                        print(f'[-] 解析文件 "{os.path.basename(fn)}" 的第 {i} 个单词时出现了编码错误')
                        filesInfo[fn]['error'].append(f'解析文件 "{fn}" 的第 {i} 个单词时出现了编码错误')
                        i -= 1
            filesInfo[fn]['total'] = i
    return wordsList, filesInfo


def printWordsTable(wordsList: List[Word.Word]):
    table = Table.Table()
    table.titles = [
        ['编号', 0, Table.Table.ALIGN_RIGHT],
        '单词',
        '释义',
        '单词出处',
        ['文件中编号', 0, Table.Table.ALIGN_RIGHT]
    ]
    for i, w in enumerate(wordsList):
        table.data.append([
            i + 1,
            w.word,
            w.mean,
            w.info.get('filepath', '') if len(w.info.get('filepath', '')) < 27 else '...' + w.info.get('filepath', '')[-27:],
            str(w.info.get('id', 0))
        ])
    table.print()


def speakWords(speaker: Speaker.Speaker, wordsList: List[Word.Word], config=None,
               before=lambda w, m: print(w + '\n' + m + '\n')):
    for w in wordsList:
        before(w.word, w.mean)
        w.speakWord(speaker, config)
        w.speakMean(speaker, config)


def printHelp(__data: list[Union[str, tuple[str, Union[str, list[tuple[str, str]]]]]]):
    print()
    # print(__data)
    for l in __data:
        if isinstance(l, str):
            print(l)
        elif isinstance(l, tuple):
            print(l[0] + ':')
            if isinstance(l[1], str):
                print(' ' * 8 + l[1])
            elif isinstance(l[1], list):
                maxWidth = 0
                for i, _ in l[1]:
                    tmpWidth = stringutils.getRealLen(i)
                    maxWidth = tmpWidth if tmpWidth > maxWidth else maxWidth
                maxWidth += 4
                for i, j in l[1]:
                    if isinstance(j, str):
                        print(' ' * 8 + i.ljust(maxWidth - stringutils.getDoubleWordsLen(i)) + j)
                    elif isinstance(j, tuple):
                        print(' ' * 8 + i.ljust(maxWidth - stringutils.getDoubleWordsLen(i)) + j[0])
                        width = [0, 0]
                        for _j in j[1]:
                            tmpWidth = [stringutils.getRealLen(_j[0].__str__()),
                                        stringutils.getRealLen(_j[1])]
                            width = [tmpWidth[0] if tmpWidth[0] > width[0] else width[0],
                                     tmpWidth[1] if tmpWidth[1] > width[1] else width[1]]
                        titleSep = True
                        print(' ' * (8 + maxWidth) + f'+-{"-" * width[0]}-+-{"-" * width[1]}-+')
                        for _j in j[1]:
                            print(' ' * (8 + maxWidth) + f'| {str(_j[0]).rjust(width[0] - stringutils.getDoubleWordsLen(_j[0].__str__()))} | {_j[1].ljust(width[1] - stringutils.getDoubleWordsLen(_j[1]))} |')
                            if titleSep:
                                print(' ' * (8 + maxWidth) + f'| {"=" * width[0]} | {"=" * width[1]} |')
                                titleSep = False
                        print(' ' * (8 + maxWidth) + f'+-{"-" * width[0]}-+-{"-" * width[1]}-+')
                    # print()
        else:
            continue
        print()
    sys.exit(1)


def wordsListToTupleList(wordsList: list[Word.Word]):
    wordsDict = []
    for w in wordsList:
        wordsDict.append((w.word, w.mean, (w.parsedWord, w.parsedMean, w.listedMean)))
    return wordsDict
