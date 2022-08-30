# LUKSense

**LUKSense is a platform for buying, selling, and tracking licenses.**
Enriched with innovative features, LUKSense offers an all-in-one solution for
license management. The platform operates on [LUKSO network](https://lukso.network/).
**The goal of LUKSense is making it as easy as possible for anyone to start
using Web 3 solutions in the same way they use Web 2.**

![LUKSense Logo](static/assets/images/logo/logo.png)

### Project Name
LUKSense
### Creator
Hesam Sameri
### Creator Contact
h.sameri[AAATTT]proton.me

**a [LUKSO Hackathon](https://lukso.network/hackathon) submisson**

## Demo dApp

**Demo dApp is available at [luksense.store](http://luksense.store)**

LSP8 contract used in the demo: [0x763b8a43321A6D45aFbADe24Ad398460F85820cf](https://explorer.execution.l16.lukso.network/address/0x763b8a43321A6D45aFbADe24Ad398460F85820cf)

## Demo video

**Demo video is available at [youtu.be/UyaAmd0jKNA](https://youtu.be/UyaAmd0jKNA)**

## Features

* A truly permissionless platform
  - No ban or removal is possible
* Fast and rich search system
  - LSP4 metadata of licenses are indexed in Elasticsearch for best search experience
* Built-in customizable gamification
  - Users earn trophies for certain actions and prestige for good behavior
* Advanced caching (i.e. Web 3 as fast as Web 2)
  - Smart contact data is cached in a local Postgresql for faster retrieval
* Built on top of LUKSO standards
  - LUKSense makes use of and is compatible with several LUKSO LSPs


## Debian/Ubuntu Setup

This installation manual assumes you have a freshly installed minimal OS.
This is tested on Ubuntu 20.04.
Slight changes in the commands might be needed for other Debian-based systems.
Don't forget to run all commands as a superuser (root).

### Pre-configuration

```
apt update
apt upgrade -y
apt install wget curl ca-certificates apt-transport-https -y
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
wget -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | tee /etc/apt/sources.list.d/elastic-8.x.list
sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ focal-pgdg main" >> /etc/apt/sources.list.d/pgdg.list'
apt update
```

### Install

```
apt install postgresql postgresql-contrib elasticsearch redis nodejs -y
```

Elasticsearch prints some post-installation info.
Make sure to write down the generated password for the elastic built-in superuser.
By the way, you can reset that password any time by issuing:

```
/path/to/elasticsearch-reset-password -u elastic
```

### Configure

Configure Elasticsearch as a service for easier management:

```
systemctl daemon-reload
systemctl enable elasticsearch.service
systemctl start elasticsearch.service
```

Make sure `pg_config` is in `PATH` environment variable.
Switch to `postgres` user to be able to access `psql` on command line.
Run `psql` and create `mainnet` and `testnet` databases.
Create tables by importing `schema.sql`:

```
psql mainnet < schema.sql
psql testnet < schema.sql
```
  
Check and edit `config.sql`.
Make sure all 'MUST_CHANGE_THIS' strings are changed.
Also make sure `storage_location` path exists for both environments.
Run the queries for both `mainnet` and `testnet` databases:

```
psql mainnet < config.sql
psql testnet < config.sql
```

You can select `site_env` in `app.py` and change it at anytime later.

Edit `/etc/postgresql/14/main/pg_hba.conf` and grant access to your OS user.

Make a virtual environment and activate it:

```
python3 -m venv venv
source venv/bin/activate
```

Install helper packages for building requirements (run as root):

```
apt install build-essential libpq-dev python3-dev postgresql-server-dev-all -y
```

Install requirements:

```
pip3 install -r requirements.txt
```

Run `index_setup.txt` in Kibana dev tools or
issue a corresponding `curl` command directly to Elasticsearch.

Install required npm packages in `lukso` and `lukso/api` directories.
Edit `lukso/lsp8.js` as desired and run it once to have an LSP8 contract.
Rename `lukso/sample_config.json` to `lukso/config.json` and fill in the empty values.
Finally, in `lukso/api/` directory, create a sqlite database named `api.db` and import `api.sql`.

### Run

All four components below must be running together, otherwise you'll face problems.

#### Python Web App

```
gunicorn -t 300 --log-level debug --workers 4 --bind 127.0.0.1:9000 app:app
```

#### Celery Backround

```
celery -A app.celery worker -E -l INFO
```

#### LUKSO Event Listener

```
cd lukso
watch -n 60 node event.js
```

#### Internal API

```
cd lukso/api
node index.js
```

## Self-governing System

LUKSense comes with a built-in self-governing system.
It prevents spam and rewards good behavior.
More info will be available here soon.


## Upcoming Features

Here is a list of WIP and upcoming features:

- [ ] Script for easy installation / Docker image
- [ ] DAO (replacing current self-governance)
