#!/usr/bin/env python3

import os
import sys
import argparse
import configparser

from Base.activity_store import ActivityStore
from Base import config as cfg


def parse_config():
    conf_parser = argparse.ArgumentParser(description=__doc__, add_help=False,
                                          formatter_class=argparse.RawDescriptionHelpFormatter)
    conf_parser.add_argument("-c", "--config",
                             help="Config file with defaults. Command line parameters will override those given in the config file. The config file must start with a \"[Defaults]\" section, followed by [argument]=[value] on each line.", metavar="FILE")
    args, remaining_argv = conf_parser.parse_known_args()

    defaults = {}
    if args.config:
        if not os.path.exists(args.config):
            raise EnvironmentError(f"Config file {args.config} doesn't exist.")
        config = configparser.ConfigParser()
        config.read([args.config])
        defaults = dict(config.items('Defaults'))
    else:
        if os.path.exists(os.path.expanduser('~/.Base/Base.conf')):
            config = configparser.ConfigParser()
            config.read([os.path.expanduser('~/.Base/Base.conf')])
            defaults = dict(config.items('Defaults'))

    parser = argparse.ArgumentParser(description='Monitor your computer activities and store them in a database for later analysis or disaster recovery.', parents=[conf_parser])
    parser.set_defaults(**defaults)
    parser.add_argument('-d', '--data-dir', help=f'Data directory for Base, where the database is stored. Remember that Base must have read/write access. Default is {cfg.DATA_DIR}', default=cfg.DATA_DIR)
    parser.add_argument('-n', '--no-text', action='store_true', help='Do not store what you type. This will make your database smaller and less sensitive to security breaches. Process name, window titles, window geometry, mouse clicks, number of keys pressed and key timings will still be stored, but not the actual letters. Key timings are stored to enable activity calculation in selfstats.')
    parser.add_argument('-r', '--no-repeat', action='store_true', help='Do not store special characters as repeated characters.')

    return parser.parse_args()


def main():
    try:
        args = vars(parse_config())
    except EnvironmentError as e:
        print(str(e))
        sys.exit(1)

    args['data_dir'] = os.path.expanduser(args['data_dir'])

    try:
        os.makedirs(args['data_dir'])
    except OSError:
        pass

    astore = ActivityStore(os.path.join(args['data_dir'], cfg.DBNAME),
                           store_text=(not args['no_text']),
                           repeat_char=(not args['no_repeat']))
    try:
        astore.run()
    except KeyboardInterrupt:
        astore.close()

if __name__ == '__main__':
    main()
