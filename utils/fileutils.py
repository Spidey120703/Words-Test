import os.path
import hashlib
import re


def mkdir(path):
    if path != '' and not os.path.isdir(path):
        os.mkdir(path)


def mkdirs(path: str):
    if path != '' and not os.path.isdir(path):
        parent = os.path.dirname(path)
        if parent != '' and not os.path.isdir(parent):
            mkdirs(parent)
        mkdir(path)


def fileGetContents(path: str) -> bytes:
    if os.path.isfile(path):
        with open(path, 'rb+') as f:
            return f.read()


def filePutContents(path: str, contents: bytes):
    mkdirs(os.path.dirname(path))
    with open(path, 'wb+') as f:
        f.write(contents)


def sha(contents: bytes):
    return hashlib.sha1(contents).hexdigest()


def getFilesList(args: list[str], pwd: str = os.getcwd()):
    fileList = []
    tempList = []
    for a in args:
        # if len(a) > 3 and a[0].isupper() and a[1] == ':' and a[2] == os.path.sep:
        if re.match(r'^([A-Z]:)?\\', a):
            tempList.append(a)
        else:
            tempList.append(os.path.abspath(os.path.join(pwd, a)))
    for t in tempList:
        if os.path.isfile(t):
            fileList.append(t)
        elif os.path.isdir(t):
            for i in os.listdir(t):
                if os.path.splitext(i)[1] == '.txt':
                    fileList.append(os.path.join(t, i))
        elif '*' in t or '?' in t:
            with os.popen(f'cmd /c dir /b "{t}" 2>NUL') as p:
                fileList.extend(getFilesList(p.read().split('\n')[:-1], os.path.dirname(t)))
    return fileList
