# lemonsqueepy

[Lemon Squeezy](https://www.lemonsqueezy.com/) with Python 🐍

## Deployment

This project should be deployed in **Debian GNU/Linux 11 (bullseye).**

First install dependencies as follow:

```bash
# Install `nginx` if you don't have.
sudo apt-get install nginx
sudo systemd enable nginx
sudo systemd start nginx

# Install `redis` if you don't have.
sudo apt-get install redis
sudo systemd enable redis
sudo systemd start redis

# Install `mongodb-org` if you don't have.
# https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-debian/
sudo apt-get install gnupg curl
curl -fsSL https://pgp.mongodb.com/server-6.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg] http://repo.mongodb.org/apt/debian bullseye/mongodb-org/6.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl enable mongod
sudo systemctl start mongod

# Install `certbot` if you don't have.
sudo apt-get install certbot
sudo apt-get install python3-certbot-nginx

# Install `pm2` if you don't have.
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
nvm install node # restart your bash, then
npm install -g pm2
pm2 install pm2-logrotate

# Install `python3` if you don't have.
sudo apt-get install python3
sudo apt-get install python3-pip

# Install `pyenv` if you don't have.
# https://github.com/pyenv/pyenv#automatic-installer
curl https://pyenv.run | bash

# Install `pipenv` if you don't have.
pip install --user pipenv

# Install all dependencies needed by this project.
git clone git@github.com:mthli/lemonsqueepy.git
cd ./lemonsqueepy/
pipenv install
pipenv install --dev
```

Before run this project:

- TODO
- Put `./lemon.mthli.com.conf` to `/etc/nginx/conf.d/` directory.
- Execute `sudo certbot --nginx -d lemon.mthli.com` to generate certificates, or
- Execute `sudo certbot renew` to avoid certificates expired after 90 days.

Then just execute commands as follow:

```bash
# Make sure you are not in pipenv shell.
pm2 start ./pm2.json
```

## License

```
lemonsqueepy - Lemon Squeezy with Python 🐍

Copyright (C) 2023  Matthew Lee

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```
