from __future__ import print_function
import argparse
import ConfigParser


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


if __name__ == '__main__':
    args = parse_arguments()
    parser = parse_configuration_file(args.configuration)
    for section in parser.sections():
        print(section)
        for option in parser.options(section):
            print('  ', option, parser.get(section, option))
