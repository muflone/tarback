import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('configuration', type=str,
                        help='configuration file to use')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='output verbose')
    args = parser.parse_args()
    print(args)
