# Wallet project 
## environment setup
### Vagrant 搭建
`vagrant up`:會建立ubuntu/xenial64的virtual machine

`vagrant reload --provision`

`vagrant ssh`:進入VM環境

### MySQL 設定
`cd provision`

`bash create_db.sh`:建立需要的wallet_db資料庫

### Django command
`source /venv/jkos/bin/activate`

`cd src/wallet`

`python3 manage.py runserver 0:8000`


### A set of runnable HTTP APIs:

#### 1. create new wallet:
`http://localhost:5566/api/user/new/`

request: curl -X POST -H "Content-Type: application/json" -d '{"name":"Bob"}' "http://localhost:5566/api/user/new/"

reply: {"error":0, "wallet_id": 1}


#### 2. Deposit to the specific wallet

`http://localhost:5566/api/wallet/deposit/`

request: curl -X POST -H "Content-Type: application/json" -d '{"wallet_id":1, "amount":12.34}' "http://localhost:5566/api/wallet/deposit/"

reply: {"error":0, "new_balance": "12.34"}


#### 3. Transfer to the specific wallet

`http://localhost:5566/api/wallet/transfer/`

request: curl -X POST -H "Content-Type: application/json" -d '{"from_wallet_id":2, "to_wallet_id": 1, "amount":12.34}' http://localhost:5566/api/wallet/transfer/

reply: {"error":0, "new_balance": "0.01"}

#### 4. A web page to allow use query the transactions from a certain wallet account by some filters.
POST Method:
`http://localhost:5566/web/wallet/statements/`

Get Method:
get all transaction statements of wallet id 1:
`http://localhost:5566/web/wallet/statements/1/0`

get recent 5 numbers of transaction statements of wallet id 1:
`http://localhost:5566/web/wallet/statements/1/5`

get recent 10 numbers of transaction statements of wallet id 2:
`http://localhost:5566/web/wallet/statements/2/10`

### One runnable unittest case

`python manage.py test`

### Gunicorn and Nginx
Gunicorn 'Green Unicorn' is a Python WSGI HTTP Server for UNIX.

Deploy Gunicorn on Nginx:

`sudo apt install nginx -y`: install Nginx

`pip install gunicorn` : install gunicorn

`pip install gevent`: install gevent

`touch etc/nginx/sites-available/wallet`: paste following block text


~~~
  server {
    listen 5678;
    server_name example.org;
    access_log  /var/log/nginx/example.log;

    location / {
        proxy_pass http://127.0.0.1:8888;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
  }
~~~

`ln  -s /etc/nginx/sites-available/wallet /etc/nginx/sites-enabled`: Create a sysbolic link to site-enabled/

### Performance Benchmark

#### run django via gunicorn with gevent worker type
`gunicorn -b 127.0.0.1:8888 -w 4 -k gevent wallet.wsgi`
#### performance test
boom "http://localhost:8080/api/wallet/deposit/" -c 10 -n 100 -m POST -D '{"wallet_id":8, "amount":5}' --content-type "applicationn/json"

#### run django via gunicorn with sync worker type
`gunicorn -b 127.0.0.1:8888 -w 4 -k sync wallet.wsgi`
#### performance test
boom "http://localhost:8080/api/wallet/deposit/" -c 10 -n 100 -m POST -D '{"wallet_id":8, "amount":5}' --content-type "applicationn/json"