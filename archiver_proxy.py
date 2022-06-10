#!/usr/bin/env python3
import ast

from caproto import ChannelType
from caproto.server import PVGroup, ioc_arg_parser, pvproperty, run
import httpx
import numpy as np

KEYS = ("mean", "std", "min", "max", "num_samples")


async def get_data(url, keys=KEYS):

    async with httpx.AsyncClient() as client:
        r = await client.get(url)
    payload = r.json()[0]
    n_vals = len(payload["data"])
    # TODO also do the alarms
    out = {k: np.zeros(n_vals) for k in keys}
    out["time"] = np.zeros(n_vals)

    # transpose the data
    for j, step in enumerate(payload["data"]):
        out["time"][j] = step["secs"]
        for k, v in zip(keys, step["val"]):
            out[k][j] = v

    return out


class ArchiverProxy(PVGroup):
    # TODO make this configurable and a template
    url = ""
    # TODO do all of the keys
    mean = pvproperty(name=":archived_24hr_mean", dtype=float, max_length=2000)
    time = pvproperty(name=":archived_24hr_timebase", dtype=float, max_length=2000)

    read_count = pvproperty(name=":read_counter", dtype=int, value=0)

    @read_count.scan(period=5)
    async def read_count(self, instance, async_lib):
        print("about to hit archiver!")
        payload = await get_data(self.url)
        for k in KEYS:
            if k not in ("time", "mean"):
                continue
            await getattr(self, k).write(payload[k])
        await instance.write(instance.value + 1)


if __name__ == "__main__":
    ioc_options, run_options = ioc_arg_parser(
        default_prefix="",
        desc="Proxy queries to the archiver to a wavefrom for phebous web.",
    )

    ioc = ArchiverProxy(**ioc_options)
    run(ioc.pvdb, **run_options)
