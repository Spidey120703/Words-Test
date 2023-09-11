import multiprocessing
import time

from tools import Speaker
from abstract import Word


class SpeakerProcess(multiprocessing.Process):
    def __init__(self, speaker: Speaker.Speaker, sleep: int = 10, word: Word.Word = None):
        super().__init__()
        self.word = word
        self.speaker = speaker
        self.sleep = sleep

    def setWord(self, word: Word.Word):
        self.word = word

    def run(self) -> None:
        while True:
            try:
                time.sleep(self.sleep)
                if self.word:
                    self.word.speakWord(self.speaker)
            except:
                pass


if __name__ == '__main__':
    start = time.perf_counter()
    while 1:
        print(str(time.perf_counter() - start))
        time.sleep(0.5)
