# Archiver Proxy

This is a small caproto IOC to proxy between the Archiver and the Pheobus web-front end to show historical traces

Start via

```bash
$ python archiver_proxy.py --list-pvs --config=config.yaml
```


The format of the configuration file is:

```yaml
- archiver_url: http://some.url.tld:port
  pvs:
  - name: PV1
    window: 24
  - name: PV2
    window: 2

- archiver_url: http://other.url.tld:port
  pvs:
  - name: PV3
    window: 36
  - name: PV4
    window: 1
```

The created PVs will be of the form

```
{SOURCE_PV}:archived_{WINDOW}h_mean
{SOURCE_PV}:archived_{WINDOW}h_timebase
{SOURCE_PV}:read_counter
```

so all PVs can not be repeated between archivers.

There are always ~800 samples independent of the time window.