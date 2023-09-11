import os.path

import pydub.exceptions
from pydub import AudioSegment
from pydub import playback
from win32com import client as win32client

from utils import httputils, coreutils, fileutils


class Speaker:
    API_WINDOWS = 0
    API_YOUDAO = 1
    API_BAIDU = 2

    LANG_ENGLISH = 0
    LANG_CHINESE = 1

    YOUDAO_TTS = 0
    YOUDAO_DICT = 1

    curApi = API_WINDOWS
    cachePath = os.path.join(os.getcwd(), 'caches')
    defaultLang = LANG_ENGLISH
    defaultConfig = {}
    curConfig = {}

    def __init__(self, api: int = API_WINDOWS, cache: str = r'.\caches', lang: int = LANG_ENGLISH):
        self.setApi(api)
        self.setCaches(cache)
        self.setLang(lang)

    def setApi(self, api: int):
        self.curApi = api

    def setCaches(self, path: str):
        self.cachePath = path

    def setLang(self, lang: int):
        self.defaultLang = lang

    def setConfig(self, config: dict):
        self.defaultConfig = config

    def downloadAudioFile(self, content: str, audioPath: str):
        if self.curApi == self.API_BAIDU:
            url = f'https://fanyi.baidu.com/gettts?lan={"zh" if self.curConfig.get("lang", self.defaultLang) else "en"}' \
                  f'&text={content}&spd={str(self.curConfig.get("speed", 3))}&source=web'
        else:
            if self.curConfig.get('domain', self.YOUDAO_TTS) == self.YOUDAO_DICT:
                url = f'https://dict.youdao.com/dictvoice?audio={content}&type={self.curConfig.get("type", 0)}' \
                      f'{"&le=chn" if self.curConfig.get("lang", self.defaultLang) == self.LANG_CHINESE else ""}'
            else:
                url = f'https://tts.youdao.com/fanyivoice?word={content}' \
                      f'&le={"chn" if self.curConfig.get("lang", self.defaultLang) == self.LANG_CHINESE else "eng"}' \
                      f'&keyfrom=speaker-target' \
                      f'{"" if self.curConfig.get("type", 0) == 0 else ("&type=" + str(self.curConfig.get("type", 0)))}'
        httputils.downloadFile(url, audioPath)

    def getAudioFilePath(self, content: str):
        audioPath = os.path.join(self.cachePath, fileutils.sha(content.encode()), str(self.curApi))
        if self.curApi == self.API_BAIDU:
            audioPath += f'{coreutils.rangeCheck(self.curConfig.get("lang", self.defaultLang), (self.LANG_ENGLISH, self.LANG_CHINESE), self.defaultLang)}' \
                         f'{coreutils.rangeCheck(self.curConfig.get("speed", 3), (1, 7), 3)}'
        else:
            audioPath += f'{coreutils.rangeCheck(self.curConfig.get("domain", self.YOUDAO_TTS), (self.YOUDAO_TTS, self.YOUDAO_DICT), self.YOUDAO_TTS)}' \
                         f'{coreutils.rangeCheck(self.curConfig.get("lang", self.defaultLang), (self.LANG_ENGLISH, self.LANG_CHINESE), self.defaultLang)}' \
                         f'{coreutils.rangeCheck(self.curConfig.get("type", 0), (0, 2), 0)}'
        if os.path.isfile(audioPath):
            return audioPath
        else:
            self.downloadAudioFile(content, audioPath)
            return audioPath

    def speak(self, content: str, config: dict = None):
        self.curConfig = config if config is not None else self.defaultConfig
        if self.curApi != 0:
            try:
                playback.play(AudioSegment.from_mp3(self.getAudioFilePath(content)))
                # self.getAudioFilePath(content)
            except pydub.exceptions.CouldntDecodeError:
                playback.play(AudioSegment.from_wav(self.getAudioFilePath(content)))
        else:
            spVoice = win32client.Dispatch('SAPI.SpVoice')
            spVoice.Rate = self.curConfig.get('rate', 0)
            spVoice.Voice = spVoice.GetVoices().Item(self.curConfig.get('voice', 0))
            spVoice.Speak(content.replace('(', '').replace(')', ''))
        if config is not None:
            self.curConfig = self.defaultConfig


if __name__ == '__main__':
    s = Speaker()
    # s.speak('optimus prime', {
    #     'rate': 0,
    #     'voice': 1
    # })
    s.setApi(1)
    s.speak('你好', config={
        'domain': 1,
        'type': 2,
        'lang': 1,
        'speed': 3
    })
    # print(coreutils.py.maxCheck(6, (1, 5), 2))
    # coreutils.printf('123')
