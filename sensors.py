#!/usr/bin/env python3

import json
import re
import os
import glob

DIR = "/sys/class/hwmon"


def read(fn):
    with open(fn) as f:
        return f.read()


def read_parse(fn):
    x = read(fn).strip()
    try:
        return int(x)
    except BaseException:
        return x


def list_hwmon():
    return sorted([f for f in os.listdir(DIR) if f.startswith("hwmon")])


def process_sensors(path):
    r = {}
    for fn in os.listdir(path):
        m = re.match(r"^(fan|in|temp|power)(\d+)_(.*)$", fn)
        if not m:
            continue

        t, i, rd = m.group(1, 2, 3)

        sens = f"{t}{i}"
        if sens not in r:
            r[sens] = {"sensor_type": t}

        r[sens][rd] = read_parse(f"{path}/{fn}")

    return r


def process_hwmon(n):
    path = f"{DIR}/{n}"
    if not os.path.exists(f"{path}/name"):
        return None, None

    name = read(f"{path}/name").strip()

    blockdev = False
    if os.path.isdir(f"{path}/device/block"):
        blockdev = os.path.basename(glob.glob(f"{path}/device/block/*")[0])

    if glob.glob(f"{path}/device/nvme*"):
        blockdev = os.path.basename(glob.glob(f"{path}/device/nvme*")[0])

    raw_devlinks = glob.glob("/dev/disk/by-id/*")
    devlinks = list(filter(lambda x: not re.search("^nvme-eui|^nvme-nvme|^wwn-0x|^scsi-[0-9]", os.path.basename(x)), raw_devlinks))
    if blockdev:
        for devlink in devlinks:
            if os.path.islink(devlink) and blockdev==os.path.basename(os.readlink(devlink)):
                name = os.path.basename(devlink)
                break
    # else:
    #     name = f"{hwm}-{name}"

    # print(name)

    return name, process_sensors(path)


r = {}

for hwm in list_hwmon():
    name, sensors = process_hwmon(hwm)
    if not sensors:
        continue

    r[name] = sensors

print(json.dumps(r, indent=2, sort_keys=True))
