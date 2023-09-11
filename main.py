try:
    import os
    import sys
    import multiprocessing

    from abstract import Command
    from commands import ConvertCommand, SearchCommand, DetectCommand, ReadCommand, ChoiceCommand, ServerCommand, \
    TestCommand
    from utils import utils
except KeyboardInterrupt:
    sys.exit(1)

availableCommands = {
    "read": [ReadCommand.ReadCommand, '阅读单词，预览词汇'],
    "search": [SearchCommand.SearchCommand, '搜索单词，在词典文件中检索'],
    "test": [TestCommand.TestCommand, '单词默写，给出释义或单词，默写单词或释义关键词'],
    "choice": [ChoiceCommand.ChoiceCommand, '单词选择，给出单词或释义，从四个可选项中选出正确释义或单词'],
    "detect": [DetectCommand.DetectCommand, '词典文件检测，检测其是否有效，预览词汇'],
    "server": [ServerCommand.ServerCommand, '移动端下载服务'],
    "convert": [ConvertCommand.ConvertCommand, '词典格式转换']
}


def main():
    usage = f'语法: {os.path.split(sys.argv[0])[1]} 命令 -选项:值 --选项=值 文件名 文件路径...'
    if len(sys.argv) < 2:
        utils.printHelp([
            usage,
            ('命令', [(i, j[1] if len(j) > 1 and isinstance(j[1], str) else '功能暂未开放') for i, j in availableCommands.items()]),
            ' * 详细信息请查看命令帮助“-h”或“--help”'
        ])
    command = sys.argv[1]
    args = sys.argv[2:]
    if command not in availableCommands:
        utils.printHelp([
            f'错误: “{command}”命令不存在',
            ('命令', [(i, j[1] if len(j) > 1 and isinstance(j[1], str) else '功能暂未开放') for i, j in availableCommands.items()]),
            ' * 详细信息请查看命令帮助“-h”或“--help”'
        ])
    command = availableCommands.get(command, [Command.Command])[0](args)
    command.exec()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
