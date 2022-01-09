# JiroAPI

> API backend built with privacy in mind for Jirotion App (a No-Fuss Tasks/Notes Management WebApp).

## Description & Features

Built using FastAPI, MongoDB, Redis, Gunicorn, NGINX & Docker.

* Scalable
* Proxied & Load Balanced
* OAuth Login using JWT
* Caching through Redis
* Data Encrypted in both Database & Cache

> Highly Secure. If you loose your login password, all your application related core data stored are lost.

## How is Data Encryption Handled?

1. Data Encryption Key & Salt Generation
    1. When a user is created, a Data Encryption Key (dek) (fernet key) & salt (bcrypt salt) is newly generated.
    2. The salt is passed into a Key Derivation Function (kdf) (bcrypt kdf) with the user's hashed password (sha256) as password to generate a unique wrapping key.
    3. Using this wrapping key (fernet key), the dek is encrypted.
    4. Only the encrypted dek and salt is stored in database which will be used to encrypt user's data
2. When User logins by providing his/her username & password
    1. The user's password (sha256 hashed) & user's salt (stored in database) is passed again into a kdf to regenerate the unique wrapping key (generated at 1.ii)
    2. Using the regenerated wrapping key, the encrypted dek (stored in database) is decrypted and is then stored at the client as an http_only cookie
3. Data Encryption & Decryption
    1. the dek stored at the client in the cookie, is used to encrypt and decrypt the data provided by user to be stored in database

## Getting Started

1. Clone this repo.
2. Configure username & password for cache (Redis) and database (MongoDB) in both .env files ([.env_template](/.env_template) & [.env_template](/api/.env_template)) and rename file to .env
    ```
    # for REDIS_PASSWD, MONGODB_PASSWD, SECRET_KEY
    $ python -c 'import secrets; print(secrets.token_urlsafe(16))'
    
    # for REDIS_CRYPTO_KEY
    $ python -c 'import secrets; import base64; import os; print(base64.urlsafe_b64encode(os.urandom(32)))'
    ```
3. As I've configured NGINX to use SSL, place the server.key and server.crt in [nginx](/nginx) folder & update server name in [defaults.conf](/nginx/defaults.conf) with your domain name
    1. if hosting app in local, refer to [this](https://devcenter.heroku.com/articles/ssl-certificate-self) guide to generate a self-signed certificate
4. Execute ```./run build``` to build & start the application container
5. Use 
    1. ```./run logs``` to tail logs (or) 
    2. ```./run status``` to check the health of running containers (or)
    3. ```./run destroy``` to bring down the app
   
Checkout [run](./run) for more available repetitive tasks

### API Health at [https://127.0.0.1/api/v1/health](https://127.0.0.1/api/v1/health)
### Swagger Docs at [https://127.0.0.1/api/v1/docs](https://127.0.0.1/api/v1/docs)

## Endpoints & Routes

```
/health
view API health and status of dependent services

/login
oauth2 login. generate jwt access token

/users/*
to add new user; get info on current user; update current user's profile; change current user's password

/tasks/*
to add new task; fetch a task or multiple tasks; update a task (change details or add to-do items or comments); delete task
```

##### Refer to the Swagger Docs at [https://127.0.0.1/api/v1/docs](https://127.0.0.1/api/vi/docs) for detailed info on schemas for each route & request method

## Future State
Both user and task data are hosted in MongoDB for the time being. It makes sense to use MongoDB to hold task related data but not for user data. So it will be migrated to PostgreSQL in future.

## License
[MIT](https://choosealicense.com/licenses/mit/)
