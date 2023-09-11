import requests
from utils import fileutils

HTTP_DEFAULT_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/89.0.4389.114 Safari/537.36',
}

HTTP_METHOD_GET = 0
HTTP_METHOD_POST = 1
HTTP_METHOD_HEAD = 2
HTTP_METHOD_PUT = 3
HTTP_METHOD_DELETE = 4
HTTP_METHOD_OPTIONS = 5


def httpGetContents(url: str, headers: dict = {}, params: dict = {}) -> bytes:
    with requests.get(url, params=params, headers={
        **HTTP_DEFAULT_HEADERS,
        **headers
    }) as r:
        return r.content


def httpPostContents(url: str, data: dict = {}, headers: dict = {}, files: dict = {}, params: dict = {}) -> bytes:
    with requests.post(url, params=params, data=data, files=files, headers={
        **HTTP_DEFAULT_HEADERS,
        **headers
    }) as r:
        return r.content


def getResourceName(url: str) -> str:
    # tmpName = os.path.split(url)[1].split('?')[0].split('#')[0]
    tmpPath = url.split('//')[1].split('/')[1:]
    if len(tmpPath) == 0:
        return 'index.html'
    tmpName = tmpPath[-1].split('?')[0].split('#')[0]
    return 'index.html' if tmpName == '' else tmpName


def downloadFile(url: str, path: str = '', headers: dict = {}, method: int = HTTP_METHOD_GET,
                 data: dict = {}, params: dict = {}):
    fileutils.filePutContents(
        path if path != '' else getResourceName(url),
        httpGetContents(url, headers, params) if method != HTTP_METHOD_POST
        else httpPostContents(url, data, headers, params=params)
    )