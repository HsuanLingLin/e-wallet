yes | sudo debconf-set-selections <<< 'mysql-server mysql-server/root_password password 1234'
yes | sudo debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password 1234'
yes | sudo apt-get -y install mysql-server
yes | sudo apt install mysql-client
yes | sudo apt install libmysqlclient-dev
yes | sudo apt install python-pymysql