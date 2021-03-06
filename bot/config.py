import os

from configargparse import ArgumentParser, ArgumentDefaultsHelpFormatter, \
    YAMLConfigFileParser

ENV_VAR_PREFIX = 'FPB_'


def setup_args_parser() -> ArgumentParser:
    parser = ArgumentParser(
        auto_env_var_prefix=ENV_VAR_PREFIX,
        default_config_files=['config.yml'],
        config_file_parser_class=YAMLConfigFileParser,
        args_for_setting_config_path=['-c', '--config-file'],
        config_arg_help_message='Config file path',
        formatter_class=ArgumentDefaultsHelpFormatter
    )

    bot_group = parser.add_argument_group('bot')
    bot_group.add_argument('--bot-token',
                           type=str,
                           help='Telegram bot token')
    bot_group.add_argument('--bot-admin',
                           type=int,
                           help='ID of bot admin')

    redis_group = parser.add_argument_group('redis')
    redis_group.add_argument('--redis-ip',
                             type=str,
                             default='redis-server',
                             help='IP of redis server')
    redis_group.add_argument('--redis-port',
                             type=int,
                             default=6379,
                             help='Port of redis server')
    redis_group.add_argument('--redis-password',
                             type=str,
                             help='Password of redis server')
    redis_group.add_argument('--redis-db',
                             type=str,
                             default='0',
                             help='Redis database number')

    return parser


def clear_env_vars():
    for env_var in tuple(os.environ):
        if env_var.startswith(ENV_VAR_PREFIX):
            os.environ.pop(env_var)
