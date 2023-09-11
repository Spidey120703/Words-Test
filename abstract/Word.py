from collections import OrderedDict

from tools import Speaker
import utils


class Word:
    """
    单词对象
    """
    word: str = ''
    mean: str = ''
    info: dict = {}
    parsedWord = []
    parsedMean = OrderedDict()
    listedMean = []
    dialogue = ''
    variant = ''

    def __init__(self, word='', mean='', info=None):
        self.info = info
        self.setWord(word)
        self.setMean(mean)

    def setWord(self, word):
        self.word = word.strip()
        # print(self.info)
        if self.info.get('sentence'):
            self.parsedWord = [self.word]
            self.variant = self.word
        elif self.info.get('phrase'):
            self.parsedWord = [self.word]
            if self.word.endswith('...'):
                self.parsedWord.append(self.word.rstrip('...').strip())
            else:
                self.parsedWord.append(self.parsedWord[-1] + ' ...')
            self.variant = self.word
        else:
            self.parsedWord = utils.parseWord(word)
            tempWords = [*self.parsedWord]
            if '/' in self.word or '-' in self.word or ('(' in self.word and ')' in self.word) and self.word in tempWords:
                tempWords.remove(self.word)
            self.variant = ', '.join(tempWords)
        self.variant = self.variant.replace(' sb.', ' somebody')
        self.variant = self.variant.replace(' sth.', ' something')
        self.variant = self.variant.replace('sb. ', 'somebody ')
        self.variant = self.variant.replace('sth. ', 'something ')

    def setMean(self, mean):
        self.mean = mean.strip()
        if self.info.get('sentence') or self.info.get('phrase'):
            _type = 0
        else:
            _type = self.info.get('mean-type')
        if _type == 0:
            self.parsedMean = {0: self.mean}
            self.listedMean = [self.mean]
            self.dialogue = self.mean
        else:
            self.parsedMean, self.listedMean = utils.parseMean(mean, _type)
            self.dialogue = utils.getDialogue(self.parsedMean, self.word)

    def speakWord(self, speaker: Speaker.Speaker, config: dict = None):
        if self.word.strip() != '':
            config = config if config is not None else {"lang": 0}
            speaker.speak(self.variant, config)

    def speakMean(self, speaker: Speaker.Speaker, config: dict = None):
        if self.dialogue.strip() != '':
            config = config if config is not None else {"lang": 1}
            speaker.speak(self.dialogue, config)

    def __str__(self):
        return f'{self.word}\r\n{self.mean}\r\n\r\n'

    def __repr__(self):
        return f'{self.word}\r\n{self.mean}\r\n\r\n'
