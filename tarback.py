from __future__ import print_function
import argparse
import ConfigParser
import datetime
import os.path
import subprocess

SNAPSHOT_FILENAME_FORMAT = '{PREFIX}_{NAME}_{DATETIME}_{TYPE}.{FORMAT}'
SNAPSHOT_DATETIME_FORMAT = '%Y-%m-%d_%H%M%S'
SNAPSHOT_PREFIX = 'backup'


class Snapshot(object):
    """
    Snapshot object representing a single snapshot instance from the
    backup filename.

    Members:
      filename:  backup filename
      extension: backup extension
      name:      snapshot name
      datetime:  snapshot date and time
      type:      snapshot type (full, diff)
    """
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
            self.datetime = datetime.datetime.strptime(
                '_'.join(fileparts[-3:-1]), SNAPSHOT_DATETIME_FORMAT)
            self.type = fileparts[-1]


class Configuration(object):
    """
    Configuration object to get data from configuration files

    Members:
      parser:    ConfigParser object
    """
    def __init__(self, filename):
        self.parser = ConfigParser.RawConfigParser()
        self.parser.optionxform = str
        self.parser.read(filename)

    def get(self, data_type, section, option, default):
        """
        Get data from the configuration object.
        Arguments:
          data_type: type of data to read (str, int, float, bool)
          section:   section to read from
          option:    option to read
          default:   default value in case the option is missing
        Returns:     value of the <data_type> type
        """
        result = default
        if self.parser.has_section(section):
            if self.parser.has_option(section, option):
                if data_type is int:
                    result = self.parser.getint(section, option)
                elif data_type is float:
                    result = self.parser.getfloat(section, option)
                elif data_type is bool:
                    result = self.parser.getboolean(section, option)
                else:
                    result = self.parser.get(section, option)
        return result

    def get_string(self, section, option, default):
        """
        Get string data from the configuration object.
        Arguments:
          section:   section to read from
          option:    option to read
          default:   default value in case the option is missing
        Returns      string value
        """
        return self.get(str, section, option, default)

    def get_int(self, section, option, default):
        """
        Get int data from the configuration object.
        Arguments:
          section:   section to read from
          option:    option to read
          default:   default value in case the option is missing
        Returns      int value
        """
        return self.get(int, section, option, default)

    def get_float(self, section, option, default):
        """
        Get float data from the configuration object.
        Arguments:
          section:   section to read from
          option:    option to read
          default:   default value in case the option is missing
        Returns      float value
        """
        return self.get(float, section, option, default)

    def get_boolean(self, section, option, default):
        """
        Get boolean data from the configuration object.
        Arguments:
          section:   section to read from
          option:    option to read
          default:   default value in case the option is missing
        Returns      boolean value
        """
        return self.get(bool, section, option, default)

    def has_section(self, section):
        """
        Check if the configuration object has the specified section.
        Arguments:
          section:   section to check
        Returns      True if the section exists, else False
        """
        return self.parser.has_section(section)

    def options(self, section):
        """
        Get the options list for the selected section.
        Arguments:
          section:   section to check
        Returns      A list of options
        """
        return self.parser.options(section)


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


def load_snapshots_list(directory):
    result = []
    for filename in sorted(os.listdir(directory)):
        if filename.startswith('backup_') and '.tar' in filename:
            snapshot = Snapshot(filename)
            result.append(snapshot)
            print(snapshot.filename)
            print('\tName:', snapshot.name)
            print('\tDate:', snapshot.datetime)
            print('\tType:', snapshot.type)


def prepare_tar_cmdline(configuration):
    directory = configuration.get_string('general', 'target', '.')

    arguments = ['tar', ]
    arguments.append('--create')
    arguments.append('--preserve-permissions')
    arguments.append('--exclude-backups')
    arguments.append('--recursion')
    arguments.append('--no-check-device')
    arguments.append('--totals')
    arguments.append('--listed-incremental={FILENAME}'.format(
        FILENAME=os.path.join(directory, 'backup.snar')))
    if configuration.get_int('general', 'followlinks', 1) == 1:
        arguments.append('--dereference')

    value = configuration.get_string('general', 'format', '')
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

    # Determine snapshot filename
    output_filename = SNAPSHOT_FILENAME_FORMAT.format(
        PREFIX=SNAPSHOT_PREFIX,
        NAME=configuration.get_string('general', 'name', 'snapshot'),
        DATETIME=datetime.datetime.now().strftime(SNAPSHOT_DATETIME_FORMAT),
        TYPE='full',
        FORMAT=output_extension)
    arguments.append('--file={FILENAME}'.format(
        FILENAME=os.path.join(directory, output_filename)))

    if configuration.has_section('dirconfig'):
        for option in configuration.options('dirconfig'):
            value = configuration.get_int('dirconfig', option, 1)
            if value == 1:
                arguments.append('--add-file={PATH}'.format(PATH=option))
            else:
                arguments.append('--exclude={PATH}'.format(PATH=option))
    return arguments


if __name__ == '__main__':
    args = parse_arguments()
    configuration = Configuration(args.configuration)
    snapshots = load_snapshots_list(
        configuration.get_string('general', 'target', '.'))
    cmdline = prepare_tar_cmdline(configuration)
    print(' '.join(cmdline))
    process = subprocess.Popen(cmdline,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    # print(stdout, stderr)
