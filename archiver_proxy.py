#!/usr/bin/env python3
import datetime
from itertools import count
from pathlib import Path
import urllib

from dateutil import parser, tz
from dateutil.relativedelta import relativedelta
import yaml

from caproto.server import PVGroup, template_arg_parser, pvproperty, run, SubGroup
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
        if isinstance(step["val"], float):
            out['mean'][j] = step["val"]
        else:
            for k, v in zip(keys, step["val"]):
                out[k][j] = v

    return out


def format_url(base: str, pv: str, since: datetime.datetime, until: datetime.datetime):
    query = {
        "pv": f"optimized_800({pv})",
        "from": since.isoformat(),
        "to": until.isoformat(),
        "fetchLatestMetadata": True,
    }
    return f"{base}/retrieval/data/getData.json?{urllib.parse.urlencode(query)}"


class ArchiverProxy(PVGroup):
    base_url: str
    target_pv: str
    # TODO do all of the keys
    mean = pvproperty(
        name=":archived_{window}_mean", dtype=float, max_length=850, value=[]
    )
    time = pvproperty(
        name=":archived_{window}_timebase", dtype=float, max_length=850, value=[]
    )

    read_count = pvproperty(name=":read_counter", dtype=int, value=0)

    def __init__(self, base_url: str, pv: str, window: int, **kwargs):
        super().__init__(**kwargs)
        self.base_url = base_url
        self.target_pv = pv
        self.window_in_hours = window

    @read_count.scan(period=60)
    async def read_count(self, instance, async_lib):
        payload = await get_data(self.get_current_url())
        for k in KEYS + ("time",):
            if k not in ("time", "mean"):
                continue
            await getattr(self, k).write(payload[k])
        await instance.write(instance.value + 1)

    def get_current_url(self):

        now = datetime.datetime.now(tz.UTC)
        then = now + relativedelta(hours=-self.window_in_hours)

        return format_url(self.base_url, self.target_pv, then, now)


if __name__ == "__main__":
    parser, split_args = template_arg_parser(
        default_prefix="",
        desc="Proxy queries to the archiver to a wavefrom for phebous web.",
    )

    parser.add_argument(
        "--config", help="path to configrutaion file to use", required=True, type=Path
    )

    args = parser.parse_args()
    ioc_options, run_options = split_args(args)
    print(args.config)
    with open(args.config, "r") as fin:
        config = list(yaml.safe_load(fin.read()))

    pv_count = count()
    body = {}
    print(config)
    for archiver in config:
        for j, pv_spec in zip(pv_count, archiver["pvs"]):

            body[f"pv{j}"] = SubGroup(
                ArchiverProxy,
                base_url=archiver["archiver_url"],
                pv=pv_spec["name"],
                prefix=pv_spec["name"].replace("{", "{{").replace("}", "}}"),
                macros={"window": f'{pv_spec["window"]}h'},
                window=pv_spec["window"],
            )
    IOCClass = type("IOCClass", (PVGroup,), body)

    ioc = IOCClass(**ioc_options)
    run(ioc.pvdb, **run_options)
