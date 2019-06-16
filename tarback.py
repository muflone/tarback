from __future__ import print_function
import argparse
import ConfigParser
import datetime
import glob
import os.path
import subprocess

SNAPSHOT_DATETIME_FORMAT = '%Y-%m-%d_%H%M%S'
SNAPSHOT_PREFIX = 'backup'


class Snapshot(object):
    def __init__(self, filename):
        self.filename = filename
        fileparts = filename.split('.', 1)
        self.extension = fileparts[1]
        fileparts = fileparts[0].split('_')
        # fileparts has the following content:
        #   [0] = SNAPSHOT_PREFIX
        #   [1..-3] = snapshot name
        #   [-3] = snapshot date
        #   [-2] = snapshot time
        #   [-1] = snapshot type
        self.name = None
        self.datetime = None
        self.type = None
        if fileparts[0] == SNAPSHOT_PREFIX:
            self.name = '_'.join(fileparts[1:-3])
            self.type = fileparts[-1]
            self.datetime = datetime.datetime.strptime(
                '_'.join(fileparts[-3:-1]), SNAPSHOT_DATETIME_FORMAT)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('configuration',
                        type=str,
                        help='configuration file to use')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='output verbose')
    args = parser.parse_args()
    return args


def parse_configuration_file(configuration_filename):
    parser = ConfigParser.RawConfigParser()
    parser.optionxform = str
    parser.read(configuration_filename)
    return parser


def get_parser_option(parser, data_type, section, option, default):
    result = default
    if parser.has_section(section):
        if parser.has_option(section, option):
            if data_type is int:
                result = parser.getint(section, option)
            elif data_type is float:
                result = parser.getfloat(section, option)
            elif data_type is bool:
                result = parser.getboolean(section, option)
            else:
                result = parser.get(section, option)
    return result


def prepare_tar_cmdline(parser):
    directory = get_parser_option(parser, str, 'general', 'target', '.')
    current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')

    arguments = ['tar', ]
    arguments.append('--create')
    arguments.append('--preserve-permissions')
    arguments.append('--exclude-backups')
    arguments.append('--recursion')
    arguments.append('--no-check-device')
    arguments.append('--totals')
    arguments.append('--listed-incremental={FILENAME}'.format(
        FILENAME=os.path.join(directory, 'backup.snar')))
    if get_parser_option(parser, int, 'general', 'followlinks', 1) == 1:
        arguments.append('--dereference')

    value = get_parser_option(parser, str, 'general', 'format', '')
    if value == 'gzip':
        arguments.append('--gzip')
        output_extension = 'tar.gz'
    elif value == 'bzip2':
        arguments.append('--bzip2')
        output_extension = 'tar.bz2'
    elif value == 'xz':
        arguments.append('--xz')
        output_extension = 'tar.xz'
    elif value == 'lzip':
        arguments.append('--lzip')
        output_extension = 'tar.lzip'
    elif value == 'lzop':
        arguments.append('--lzop')
        output_extension = 'tar.lzop'
    elif value == 'lzma':
        arguments.append('--lzma')
        output_extension = 'tar.lzma'
    elif value == 'zstd':
        arguments.append('--zstd')
        output_extension = 'tar.zstd'
    else:
        output_extension = 'tar'

    # Loads the snapshots list
    filename_length = (len('backup_') +
                       len(current_time) +
                       1 +
                       len(output_extension))
    snapshots_list = []
    for filename in sorted(os.listdir(directory)):
        if filename.startswith('backup_') and '.tar' in filename:
            print(filename)
            snapshots_list.append(filename)
    # Determine snapshot filename
    output_filename = 'backup_{DATETIME}.{EXTENSION}'.format(
        DATETIME=current_time, EXTENSION=output_extension)
    arguments.append('--file={FILENAME}'.format(
        FILENAME=os.path.join(directory, output_filename)))

    if parser.has_section('dirconfig'):
        for option in parser.options('dirconfig'):
            value = get_parser_option(parser, int, 'dirconfig', option, 1)
            if value == 1:
                arguments.append('--add-file={PATH}'.format(PATH=option))
            else:
                arguments.append('--exclude={PATH}'.format(PATH=option))


    return arguments


if __name__ == '__main__':
    args = parse_arguments()
    parser = parse_configuration_file(args.configuration)
    cmdline = prepare_tar_cmdline(parser)
    print(' '.join(cmdline))
    process = subprocess.Popen(cmdline)
    process.communicate()
