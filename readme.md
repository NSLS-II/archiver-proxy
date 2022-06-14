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
  - PV1
  - PV2
- archiver_url: http://other.url.tld:port
  pvs:
  - PV3
  - PV4
```

The created PVs will be of the form

```
{SOURCE_PV}:archived_24hr_mean
{SOURCE_PV}:archived_24hr_timebase
{SOURCE_PV}:read_counter
```

so all PVs can not be repeated between archivers.