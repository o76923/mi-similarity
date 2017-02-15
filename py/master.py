import asyncio
from itertools import combinations
from os import getenv
import aioredis
import aioprocessing
import math
from multiprocessing import cpu_count

from py.algorithm import clean_string
from py.worker import init_worker

loop = asyncio.get_event_loop()
filename = getenv("TARGET", "variable_definition")


class Master(object):
    batch_size = 250
    publish_channel = "task_created:1"
    listen_channel = "task_created:1"
    unprocessed = "unprocessed"

    def __init__(self):
        self.sentences = dict()
        self.batch_count = 0

    def load_sentences(self):
        with open("/app/data/%s.txt" % filename) as in_file:
            in_file.readline()
            raw_sentences = {x[0]: x[1] for x in [l.split("\t") for l in in_file.readlines()]}
        print("loaded sentences")
        self.sentences = {k: clean_string(v) for k, v in raw_sentences.items()}
        print("cleaned sentences")
        return self.sentences

    async def pairs_to_redis(self):
        pairs = ["%s_%s" % (p[0], p[1]) for p in combinations(self.sentences.keys(), 2)]
        print("made pairs")
        conn = await aioredis.create_redis(('localhost', 6379), password='foobared', encoding="utf-8")
        self.batch_count = math.ceil(len(pairs)/self.batch_size)
        for i in range(math.ceil(self.batch_count/100)):
            pair_batch = pairs[i*self.batch_size*100:(i+1)*self.batch_size*100]
            conn.sadd(self.unprocessed, *pair_batch)
            print("added batch %d/%d" % (i, self.batch_count/100))
        conn.close()
        print("sent pairs to redis")

    async def get_results(self):
        redis = await aioredis.create_redis(('localhost', 6379), password='foobared', encoding="utf-8")
        row_count = 0
        with open("/app/data/%s.csv" % filename, "w") as o:
            for left in self.sentences:
                key = "sim_%s" % left
                async for right, sim in redis.ihscan(key):
                    row_count += 1
                    o.write("%s,%s,%s\n" % (left, right, sim))
        print("wrote rows", row_count)

if __name__ == "__main__":
    m = Master()
    manager = aioprocessing.AioManager()
    sentence_dict = manager.dict()
    sentence_dict = m.load_sentences()
    batch_no = manager.Value('i', 0)

    loop.run_until_complete(m.pairs_to_redis())
    print("pairs into redis")

    workers = []
    for i in range(cpu_count() - 1):
        workers.append(aioprocessing.AioProcess(target=init_worker, args=(sentence_dict, batch_no, m.batch_count)))
        workers[-1].start()
    print("workers created")
    for w in workers:
        w.join()

    loop.run_until_complete(m.get_results())
