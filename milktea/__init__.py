from os import path

from nonebot import init, load_builtin_plugins, load_plugins, run


def main(config):
    init(config)
    load_builtin_plugins()
    load_plugins(path.join(path.dirname(__file__), 'plugins'),
                 'milktea.plugins')
    run()
