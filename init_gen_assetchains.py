#!/usr/bin/env python3
from jinja2 import Environment, FileSystemLoader
from ruamel.yaml import YAML
import requests
import socket
import shlex
import subprocess
import time
import argparse
# import random
# import sys
import configparser

yaml = YAML(typ='safe', pure=True)
yaml.default_flow_style = True
# yaml.preserve_quotes = True

# Load data from YAML into Python dictionary
# config_data = yaml.load(open('./yaml/data.yaml'))

asset_data_url = ("https://raw.githubusercontent.com/patchkez/kmdplatform/"
    "master/yaml/data.yaml")
dev_asset_data_url = ("https://raw.githubusercontent.com/patchkez/kmdplatform/"
    "master/yaml/dev_data.yaml")


# def run_config_data(args):
#     if args.branch == 'dev':
#         r = requests.get(dev_asset_data_url)
#     elif args.branch == 'prod':
#         r = requests.get(asset_data_url)
#     config_data = yaml.load(r.text)
#     return(config_data)


# Load Jinja2 template
env = Environment(loader=FileSystemLoader('./templates/'), trim_blocks=True, lstrip_blocks=True)


def seed_ip():
    return socket.gethostbyname(config_data['seed_host'])


# def random_gen():
#     random_int = random.randint(0, 32767)
#     # print('random is:', random_int)
#     if random_int % 10 == 1:
#         gen_param = "-gen"
#     else:
#         gen_param = ""
#     return gen_param
#
#
# def komodod_command(assetname, asset_amount):
#     return "komodod -pubkey=$PUBKEY -ac_name=" + assetname + " " + "-ac_supply=" + \
#         asset_amount + " " + "-addnode=" + seed_ip() + " " + random_gen()
#     return

def read_ini():
    config = configparser.ConfigParser()
    config.read('config.ini')
    assetchains = config['ASSETCHAINS']
    mined_coins = assetchains['mined_coins'].split(", ")
    delay_asset = float(assetchains['delay_asset'])
    return(mined_coins, delay_asset)


def generate_docker_compose(mined_coins):
    template = env.get_template('docker-compose-template.conf.j2')
    templatized_config = template.render(items=config_data['assetchains'], seed_ip=seed_ip(),
        mined=mined_coins)

    fo = open('docker-compose_assets.yml', 'w')
    fo.write(templatized_config)
    fo.close()


def run_assetchains(mined_coins, delay_assets):
    bash_template = env.get_template('assetchains.j2')
    bash_templatized_config = bash_template.render(items=config_data['assetchains'],
        seed_ip=seed_ip(), mined=mined_coins)

    fa = open('assetchains', 'w')
    fa.write(bash_templatized_config)
    fa.close()

    # Remove empty strings
    assetchains = list(filter(None, bash_templatized_config.split("\n")))
    for assetchain_command in assetchains:
        args = shlex.split(assetchain_command)
        # print("Line", args)
        p = subprocess.Popen(args)
        time.sleep(delay_assets)

# print('Writing config...')
# with open("docker-compose_assets.yml", 'w') as newconf:
#    yaml.dump(templatized_config, newconf)


def main():
    mined_coins = read_ini()[0]
    delay_assets = read_ini()[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--assetchains",
                        help="Run assetchains", action="store_true")
    parser.add_argument("-g", "--generate",
                        help="Generate docker-compose.yml for assetchains", action="store_true")
    parser.add_argument("-b", dest="branch",
                        help="Specify env - 'dev' or 'prod'", action="store", required=True)
    args = parser.parse_args()

    global config_data
    if args.branch == 'dev':
        r = requests.get(dev_asset_data_url)
    elif args.branch == 'prod':
        r = requests.get(asset_data_url)
    config_data = yaml.load(r.text)

    if args.assetchains:
        print("Executing assetchains:")
        run_assetchains(mined_coins, delay_assets)
    elif args.generate:
        print("Creating new docker compose file for assetchains:")
        generate_docker_compose(mined_coins)
    else:
        wrong_arg_msg = "Unknown option!"
        print(wrong_arg_msg)


if __name__ == "__main__":
    main()
    # read_ini()
