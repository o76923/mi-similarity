import asyncio
from collections import defaultdict

import aioredis
from os import getenv

from py.algorithm import MihalceaSentSimBNC

loop = asyncio.get_event_loop()
filename = getenv("TARGET", "variable_definition")


def init_worker(sentence_dict, batch_no, batch_count):
    w = Worker()
    print("worker started")
    loop.run_until_complete(w.main(sentence_dict, batch_no, batch_count))
    print("worker finished")


class Worker(object):
    batch_size = 250
    unprocessed = "unprocessed"

    def __init__(self):
        self.mi = MihalceaSentSimBNC()

    def calculate_similarities(self, pairs, sentence_dict):
        ret = []
        for l, r in pairs:
            ret.append((l, r, self.mi.similarity(sentence_dict[l], sentence_dict[r])))
        return ret

    async def sims_to_redis(self, sims):
        sim_dict = defaultdict(dict)
        for l, r, s in sims:
            sim_dict[l][r] = s
        redis = await aioredis.create_redis(('localhost', 6379), password='foobared', encoding="utf-8")
        for k, v in sim_dict.items():
            await redis.hmset_dict("sim_%s" % k, v)
        redis.close()

    async def main(self, sentence_dict, batch_no, batch_count):
        redis = await aioredis.create_redis(('localhost', 6379), password='foobared', encoding="utf-8")
        continue_flag = True
        while continue_flag:
            batch = []
            for i in range(self.batch_size):
                pair = await redis.spop(self.unprocessed)
                if pair is not None:
                    batch.append(pair)
                else:
                    continue_flag = False
                    break
            if len(batch) > 0:
                pairs = [p.split("_") for p in batch]
                sims = self.calculate_similarities(pairs, sentence_dict)
                await self.sims_to_redis(sims)
                batch_no.value += 1
                print("Batch {:>9,d} / {:>9,d}".format(batch_no.value, batch_count))
            else:
                continue_flag = False
