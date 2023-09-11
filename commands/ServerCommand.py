import collections
import os.path
import random
import socket
import sys
import threading
import time

import psutil

from abstract import Command
from tools import Table
from utils import fileutils


class ServerCommand(Command.Command):
    name = 'server'
    description = '说明: 开启服务器，用于移动端接收功能。'

    addresses = []

    @staticmethod
    def getAddress():
        result = collections.OrderedDict()
        addrs = psutil.net_if_addrs()
        for i in addrs:
            for j in addrs[i]:
                if j.family == 2 and not j.address.startswith('169.254'):
                    result[i] = result.get(i, [])
                    result[i].append(j.address)
        return list(result.items())

    def __init__(self, args: list[str] = []):
        self.addresses = ServerCommand.getAddress()
        self.options.append(['host', 'a', 'host', '服务监听的主机名或地址，默认为空', str, '主机名', [
            ('来源', '地址'),
            ('主机名', socket.gethostname()),
            *[j for i in [[(i[0], i[1][0])] + [('', j) for j in i[1][1:]] for i in self.addresses] for j in i]
        ]])
        self.options.append(['port', 'p', 'port', '服务监听的端口，默认随机生成，范围在 1 到 65535 之间。', int, (1, 65535)])
        self.options.append(['once', 'o', 'once', '只接受一次下载，下载一次后自动关闭，默认是不限次数。'])
        self.options.append(['encode', 'e', 'encode', '字符编码，兼容词典文件名中的中文字符，默认为安卓支持的UTF-8编码，Windows端推荐使用GBK编码', int, (0, 1), [
            ('值', '编码'),
            ('0', 'UTF-8，兼容 Linux 的编码格式'),
            ('1', 'GBK，兼容 Windows 的编码格式'),
        ]])
        super().__init__(args)

    def zipContent(self):
        zipFilesList = []
        for file in self.filesList:
            zipFilesList.append((os.path.basename(file).encode('gbk' if self.args.get('encode', 0) == 1 else 'utf-8'), fileutils.fileGetContents(file)))
        # fileutils.filePutContents('z.zip', deflateZip(zipFilesList))
        return deflateZip(zipFilesList)

    @staticmethod
    def task(serverSock, content, once):
        try:
            while True:
                clientSock, clientAddr = serverSock.accept()
                # print(f'[*] [{time.strftime("%Y-%m-%d %H:%M:%S")}] 客户端 "{clientAddr[0]}:{clientAddr[1]}" 访问了此服务')
                requestRecv = clientSock.recv(2048)
                try:
                    requestUri = requestRecv.splitlines()[0].split(b' ')[1]
                except IndexError:
                    clientSock.close()
                    continue
                if requestUri == b'/dicts.zip':
                    print(f'[+] [{time.strftime("%Y-%m-%d %H:%M:%S")}] 客户端 "{clientAddr[0]}:{clientAddr[1]}" 下载了文件')
                    responseContent = b'HTTP/1.1 200 OK\r\n' \
                                      b'Server: Apache/2.5.0 (macOS) PHP/10.0.0\r\n' \
                                      b'Date: ' + time.strftime('%A, %d %B %Y %H:%M:%S GMT', time.gmtime()).encode() + b'\r\n' \
                                      b'Content-Type: application/x-zip-compressed\r\n' \
                                      b'Content-Length: ' + len(content).__str__().encode() + b'\r\n' \
                                      b'Content-Disposition: attachment;filename=dicts.zip\r\n' \
                                      b'Connection: close\r\n' \
                                      b'\r\n' \
                                      + content
                    clientSock.send(responseContent)
                    # if self.args.get('once'):
                    #     break
                    if once:
                        break
                clientSock.close()
        except (OSError, KeyboardInterrupt):
            pass

    # def argsHandle(self, args: list[str]):
    #     filesArgs = self._argsHandle(args)
    #     self.filesList = fileutils.getFilesList(filesArgs)

    def exec(self):
        super().exec()
        # print((self.args.get('host', ''), self.args.get('port', random.randint(1024, 65535))))
        host = self.args.get('host', '')
        port = self.args.get('port', random.randint(1024, 65535))
        serverSock = socket.socket()
        serverSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        while True:
            try:
                print(f'[*] 正在尝试监听地址"{host}:{port}"...')
                serverSock.bind((host, port))
                print(f'[+] 地址"{host}:{port}"监听成功。')
                break
            except KeyboardInterrupt:
                print('[-] 您中断了监听。')
                break
            except socket.error:
                host = self.args.get('host', '')
                port = self.args.get('port', random.randint(1024, 65535))
                print(f'错误: 地址"{host}:{port}"监听出错，正在重试...')
        serverSock.listen(1)
        if len(host) == 0:
            table = Table.Table()
            table.titles.append('网络适配器')
            table.titles.append('地址')
            table.data.append(['主机名', f'http://{socket.gethostname()}{f":{port}" if not port == 80 else ""}/dicts.zip'])
            for i, a in self.addresses:
                for j in a:
                    table.data.append([i, f'http://{j}{f":{port}" if not port == 80 else ""}/dicts.zip'])
            print(f'[*] 请复制以下有效链接到移动端中下载，目前程序无法检测移动端和PC端的通讯')
            table.print()
        else:
            print(f'[*] 请复制链接 http://{host}{f":{port}" if not port == 80 else ""}/dicts.zip 到移动端中下载')
        content = self.zipContent()
        thread = threading.Thread(target=ServerCommand.task, args=(serverSock, content, self.args.get('once')))
        thread.daemon = True
        thread.start()
        while True:
            try:
                if not thread.is_alive():
                    break
                time.sleep(0.1)
            except KeyboardInterrupt:
                print('[-] 您中断了监听。')
                break
        serverSock.close()
        sys.exit(0)


def deflateZip(filelist):
    def getBinDatetime(t=time.time()):
        t = time.localtime(t)
        year, month, day, hour, minute, second = [int(i) for i in time.strftime("%Y %m %d %H %M %S", t).split()]
        if year < 1980: year, month, day, hour, minute, second = 1980, 1, 1, 0, 0, 0
        return (year - 1980) << 25 | month << 21 | day << 16 | hour << 11 | minute << 5 | second << 1

    def crc32(__data: bytes):
        # 0x104c11db7 0b100000100110000010001110110110111
        # 0x1db710641 0b111011011011100010000011001000001
        l = len(__data) * 8
        binData = __data
        __data = 0
        for i in range(len(binData)):
            __data |= binData[i] << 8 * i
        __data ^= 0xffffffff
        i = 0
        while not __data & 1:
            __data >>= 1
            i += 1
        while i < l:
            __data ^= 0x1db710641
            while not __data & 1 and i < l:
                __data >>= 1
                i += 1
        __data ^= 0xffffffff
        return __data

    import zlib
    import struct
    fileInfoList = []
    data = b''
    for f in range(len(filelist)):
        fileinfo = [len(data)]
        if isinstance(filelist[f], bytes):
            filename = filelist[f]
            fileContent = b''
            lastModified = time.time()
        else:
            if len(filelist[f]) == 2:
                filename, fileContent, lastModified = bytes(filelist[f][0]), bytes(filelist[f][1]), time.time()
            elif len(filelist[f]) == 1:
                filename, fileContent, lastModified = bytes(filelist[f][0]), b'', time.time()
            elif len(filelist[f]) == 0:
                break
            else:
                filename, fileContent, lastModified = bytes(filelist[f][0]), bytes(filelist[f][1]), float(filelist[f][2])
        compressedContent = zlib.compress(fileContent)[2:-4]
        fileHeadData = b'\x50\x4b\x03\x04'  # Local file header signature
        fileHeadData += b'\x14\x00'  # Version needed to extract (minimum)
        fileHeadData += b'\x00\x00'  # General purpose bit flag
        fileHeadData += b'\x08\x00'  # Compression method
        fileHeadData += struct.pack('L', getBinDatetime(lastModified))  # File last modification time and date
        fileHeadData += struct.pack('L', crc32(fileContent))  # CRC-32
        fileHeadData += struct.pack('L', len(compressedContent))  # Compressed size
        fileHeadData += struct.pack('L', len(fileContent))  # Uncompressed size
        fileHeadData += struct.pack('H', len(filename))  # File name length
        fileHeadData += b'\x00\x00'  # Extra field length
        fileHeadData += filename  # File name
        fileHeadData += compressedContent  # Compressed data
        data += fileHeadData
        fileinfo.append(filename)
        fileinfo.append(len(fileContent))
        fileinfo.append(len(compressedContent))
        fileinfo.append(lastModified)
        fileInfoList.append(fileinfo)
    cdfhLen = len(data)  # ZIP central directory file header length
    for fileOffset, filename, uncompressLen, compressedLen, lastModified in fileInfoList:
        data += b'\x50\x4b\x01\x02'  # Signature
        data += b'\x14\x00'  # Version made by
        data += b'\x14\x00'  # Version needed to extract (minimum)
        data += b'\x00\x00'  # General purpose bit flag
        data += b'\x08\x00'  # Compression method
        data += struct.pack('L', getBinDatetime(lastModified))  # File last modification time and date
        data += struct.pack('L', crc32(fileContent))  # CRC-32
        data += struct.pack('L', compressedLen)  # Compressed size
        data += struct.pack('L', uncompressLen)  # Uncompressed size
        data += struct.pack('H', len(filename))  # File name length
        data += b'\x00\x00'  # Extra field length
        data += b'\x00\x00'  # Extra comment length
        data += b'\x00\x00'  # Disk number where file starts
        data += b'\x01\x00'  # Internet file attributes
        data += b'\x20\x00\x00\x00'  # External file attributes
        data += struct.pack('L', fileOffset)  # ZIP local file header
        data += filename  # File name
    cdLen = len(data) - cdfhLen  # Size of central directory (bytes)
    data += b'\x50\x4b\x05\x06'  # Signature
    data += b'\x00\x00'  # Number of this disk
    data += b'\x00\x00'  # Disk where central directory starts
    data += struct.pack(b'H', len(filelist))  # Number of central directory records on this disk
    data += struct.pack(b'H', len(filelist))  # Total number of central directory records
    data += struct.pack(b'L', cdLen)  # Size of central directory (bytes)
    data += struct.pack(b'L', cdfhLen)  # ZIP central directory file header length
    data += b'\x00\x00'  # Comment length
    # print repr(data)
    return data
