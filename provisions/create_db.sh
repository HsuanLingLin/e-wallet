# create db_wallet DATABASE and wallet_db_admin USER
mysql -uroot -p1234 -Bse "CREATE DATABASE wallet_db;
CREATE USER 'wallet_db_admin'@'localhost' IDENTIFIED BY '1234';
GRANT ALL PRIVILEGES ON wallet_db.* TO 'wallet_db_admin'@'localhost';
FLUSH PRIVILEGES;"
# migrate
cd src/wallet
python manage.py makemigrations app
python manage.py migrate