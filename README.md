In order to run client, you'll need to point `OPTIMUS_TESTS_CONFIG` env variable to file with contents like:
```
client_cert: /path/to/client/cert.crt
client_key: /path/to/client/key.key
ca_cert: /path/to/ca/cert.crt
connect_to: 127.0.0.1:50051
db_uri: postgres://localhost/optimus?sslmode=disable
```