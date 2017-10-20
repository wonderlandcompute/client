In order to run client, you'll need to point `DISNEYLAND_CLIENT_CONFIG` env variable to some YAML file with contents like:
```
client_cert: /path/to/client/cert.crt
client_key: /path/to/client/key.key
ca_cert: /path/to/ca/cert.crt
connect_to: 127.0.0.1:50051
```
how to use `DisneylandClient`: [example](examples/example.ipynb)
