add-apt-repository ppa:deadsnakes/ppa
apt-get update
yes | apt-get install python3.6

apt-get install python3.6-venv
mkdir -p /venv/
python3.6 -m venv /venv/jkos
source /venv/jkos/bin/activate

yes | apt-get install libmysqlclient-dev
yes | apt-get install gcc
yes | apt-get install python3.6-dev
pip install -r ./requirements.txt

