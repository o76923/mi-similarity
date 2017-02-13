import asyncio
import json
from collections import defaultdict

import aioredis
from os import getenv

from py.algorithm import MihalceaSentSimBNC, clean_string

loop = asyncio.get_event_loop()
filename = getenv("TARGET", "variable_definition")


def init_worker(sentence_dict):
    w = Worker()
    loop.run_until_complete(w.start_listener(sentence_dict))


class Worker(object):
    listen_channel = "task_created:1"

    def __init__(self):
        self.mi = MihalceaSentSimBNC()
        loop.run_until_complete(self._initialize())

    async def _initialize(self):
        self.redis_listen = await aioredis.create_redis(('localhost', 6379), password='foobared', encoding="utf-8")
        self.ch, = await self.redis_listen.subscribe(self.listen_channel)

    def calculate_similarities(self, pairs, sentence_dict):
        ret = []
        for l, r in pairs:
            ret.append((l, r, self.mi.similarity(sentence_dict[l], sentence_dict[r])))
        return ret

    async def sims_to_redis(self, sims):
        sim_dict = defaultdict(dict)
        newly_processed = ["%s_%s" % (s[0], s[1]) for s in sims]
        print("newly_processed", newly_processed)
        for l, r, s in sims:
            sim_dict[l][r] = s
        redis = await aioredis.create_redis(('localhost', 6379), password='foobared')
        for k, v in sim_dict.items():
            await redis.hmset_dict("sim_%s" % k, v)
        await redis.srem("unprocessed", *newly_processed)
        redis.close()

    async def start_listener(self, sentence_dict):
        async for msg in self.ch.iter(encoding="utf-8", decoder=json.loads):
            if msg["type"] == "pair_request":
                pairs = [p.split("_") for p in msg["data"]["pairs"]]
                print("pairs", pairs)
                sims = self.calculate_similarities(pairs, sentence_dict)
                await self.sims_to_redis(sims)
            elif msg["type"] == "control":
                if msg["command"] == "shutdown":
                    break
