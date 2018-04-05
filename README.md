# Dockerized Komodo Notary Node

This is preparation to run Komodo platform in K8/Openshift environment. In first iteration, the goal is
to cut down Komodo/Bitcoin/Iguana in its own containers. 1 container = 1 process. For assetchains, there
is also 1 container running per coin. 

## Host preparation
### Prerequisities
- docker
- docker-compose (can be started from container)

### Create users and groups on host:
```
groupadd -g 3001 bitcoin
groupadd -g 3003 komodo
groupadd -g 3004 iguana
groupadd -g 3005 shared
groupadd -g 3006 kmdadm
groupadd -g 3007 chips
useradd -u 3001 -g bitcoin -G shared -m -d /home/bitcoin bitcoin
useradd -u 3003 -g komodo -G shared -m -d /home/komodo komodo
useradd -u 3004 -g iguana -G shared -m -d /home/iguana iguana
useradd -u 3006 -g kmdadm -G shared -m -d /home/kmdadm kmdadm
useradd -u 3007 -g chips -G shared -m -d /home/chips chips
passwd kmdadm
```
### Generate random passphrase which will be used for Iguana wallet
```
< /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c${1:-64};echo;
```


### Modify .env file and point variables to place where data for each volume can be stored
- see .env.example how .env should look like
```
...
BITCOIN_DATA=/mnt/docker/bitcoin_data
KOMODO_DATA=/mnt/docker/komodo_data
IGUANA_DATA=/mnt/docker/iguana_data
CHIPS_DATA=/mnt/docker/chips_data
SHARED_DATA=/mnt/docker/shared_data
...
```
Replace IGUANA_WALLET_PASSPHRASE with the one generated above. Make sure you safely store it!

### Source .env file
``` 
source .env
```

### Create directories with proper permissions and ownership
```
mkdir ${BITCOIN_DATA} -m 0750 && chown bitcoin:shared -R ${BITCOIN_DATA}
mkdir ${KOMODO_DATA} -m 0750 && chown komodo:shared -R ${KOMODO_DATA}
mkdir ${IGUANA_DATA} -m 0750 && chown iguana:shared -R ${IGUANA_DATA}
mkdir ${CHIPS_DATA} -m 0750 && chown chips:shared -R ${CHIPS_DATA}
mkdir ${SHARED_DATA} -m 0750 && chown iguana:shared -R ${SHARED_DATA}
```

### Prepare storage for docker layers/images - xfs+overlay2
https://docs.docker.com/storage/storagedriver/device-mapper-driver/

## First init - Start everything up
Docker images are built automatically by running `docker-compose run <service>`. You can build images manually by executing:
```
docker-compose build bitcoin
docker-compose build komodo
docker-compose build iguana
docker-compose build chips
```
or if you want to build dev branch of iguana
```
docker-compose -f docker-compose.yml -f docker-compose-dev.yml build --no-cache iguana
```

First startup of containers will create needed config files. Some files are stored on shared volumes, so other containers can access generated keys.
```
docker-compose run --rm bitcoin
docker-compose run --rm komodo
docker-compose run --rm chips
docker-compose run --rm iguana
```
or
```
docker-compose up #(not tested yet)
```

For starting iguana dev container start:
```
docker-compose -f docker-compose.yml -f docker-compose-dev.yml run --rm iguana
```

## Import of privkeys
Run these commands one by one.

We need to create iguana wallet. IGUANA_WALLET_PASSPHRASE variable inside .env file is used to pass passphrase into container.
### Create Iguana wallet
Stop bitcoin service now, iguana in basilisk mode is trying start something on port 8332 (bitcoind default rpc port).
```
docker-compose run --rm iguana first_time_init
```
or in testnet:
```
docker-compose -f docker-compose.yml -f docker-compose-dev.yml run --rm iguana first_time_init
```

### Import the privkey of your BTCD address into Komodo
Keep bitcoind stopped.
```
docker-compose run --rm komodo import_key
```

### Import BTC privkey into Bitcoin
Stop iguana now because it occupies port 8332 and start bitcoind:
```
docker-compose run --rm bitcoin
```

Import privkey:
```
docker-compose run --rm bitcoin import_key
```

### Import BTCD privkey into Chips
Import privkey:
```
docker-compose run --rm chips import_key
```



Stop all containers now.

## Start everything with pubkey
All config files were generated and stored to corresponding volumes. Each container has entrypoint script which detects e.g. if pubkey file exists and starts daemon with different arguments.


```
docker-compose run --rm bitcoin
docker-compose run --rm komodo
docker-compose run --rm chips
docker-compose run --rm iguana
```
`docker-compose up` should also start all containers, but did not have time to test it.


TODO:
- monitoring of logs
- files on komodo volume are created with wrong permissions 


## Enable python virtualenv
Install virtualenv on Centos:
```
yum install python2-pip
pip install -U virtualenv

```

This step is needed to download python packages into virtualenv (to do not mess with system python packages):
```
virtualenv -p python3 komodotools_venv
source komodotools_venv/bin/activate
pip install -Ur requirements.txt

```
### Generate docker-compose config for assetchains

This script should download yaml file with all assetchains and all its data and will create:
- docker-compose_assets.yml yaml file which can be used to spin up containers
- bash/python script which will allow to run new ./assetchains script [WIP]
```
./init_gen_assetchains.py          
usage: init_gen_assetchains.py [-h] [-r] [-g] -b BRANCH
init_gen_assetchains.py: error: the following arguments are required: -b
```

Example:
To generate docker-compose.yml file for DEV/TEST assetchains:
```
./init_gen_assetchains.py -b dev -g
Creating new docker compose file for assetchains:
```



Start all assetchains:
```
docker-compose -f docker-compose_assets.yml up
```

To stop all assetchains:
```
docker-compose -f docker-compose_assets.yml down
```

Import privkey into assetchains (DEV/TEST):
```
docker exec -it <id_of_komodo_container> bash
cd ~/komodo/src
./komodo-cli -ac_name=BEER importprivkey U*************
./komodo-cli -ac_name=PIZZA importprivkey U*************
```


### Start from scratch - TEST node only
```
rm ${SHARED_DATA}/****
rm ${BITCOIN_DATA}/.bitcoin/wallet.dat
rm ${BITCOIN_DATA}/.bitcoin/bitcoin.conf
rm ${KOMODO_DATA}/wallet.dat
rm ${KOMODO_DATA}/komodo.conf
```
wallet.dat/bitcoin.conf/komodo.conf files are created upon first start if they do not exist.


### TODO
- containers are not waiting for their dependencies
  - this can be done by using depends_on directive in docker-compose file
- iguana does not receive signal when  Ctrl+C is pressed (when iguana runs in foreground)
- services must run in host mode, otherwise ports are not listening on localhost
- noticed this error in komodod console
```
ERROR: Write: Failed to open file /home/komodo/.komodo/peers.dat.f7d9
```

- iguana shows this message when first_time_init is run
```
couldnt load (confs/969559dcebfb568349d19bff7a314eff4777ed7b7ec79f6980784c9d64d55b6d)
```
