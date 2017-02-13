import asyncio
import json
from itertools import combinations
from os import getenv
import aioredis
import aioprocessing
import math

from py.algorithm import clean_string
from py.worker import init_worker

loop = asyncio.get_event_loop()
filename = getenv("TARGET", "variable_definition")


class Master(object):
    batch_size = 100
    publish_channel = "task_created:1"
    listen_channel = "task_created:1"
    unprocessed_set = "unprocessed"

    def __init__(self):
        self.sentences = dict()
        loop.run_until_complete(self._initialize())

    async def _initialize(self):
        self.redis_publish = await aioredis.create_redis(('localhost', 6379), password='foobared', encoding="utf-8")
        self.redis_listen = await aioredis.create_redis(('localhost', 6379), password='foobared', encoding="utf-8")
        self.ch,  = await self.redis_listen.subscribe(self.listen_channel)

    def load_sentences(self):
        with open("/app/data/%s.txt" % filename) as in_file:
            in_file.readline()
            raw_sentences = {x[0]: x[1] for x in [l.split("\t") for l in in_file.readlines()[:25]]}
        print("loaded sentences")
        self.sentences = {k: clean_string(v) for k, v in raw_sentences.items()}
        print("cleaned sentences")

    async def pairs_to_redis(self):
        pairs = ["%s_%s" % (p[0], p[1]) for p in combinations(self.sentences.keys(), 2)]
        conn = await aioredis.create_redis(('localhost', 6379), password='foobared', encoding="utf-8")
        for i in range(math.ceil(len(pairs)/100)):
            pair_batch = pairs[i*100:(i+1)*100]
            conn.sadd(self.unprocessed_set, *pair_batch)
            print("added batch")
        conn.close()
        print("sent pairs to redis")

    async def make_iterator(self):
        batch = []
        print("started make iterator")
        card_check = await aioredis.create_redis(('localhost', 6379), password='foobared', encoding="utf-8")
        continue_flag = True
        while continue_flag:
            scan = await aioredis.create_redis(('localhost', 6379), password='foobared', encoding="utf-8")
            unprocessed_rows = await card_check.scard(self.unprocessed_set)
            if unprocessed_rows > 1:
                async for row in scan.isscan(self.unprocessed_set):
                    batch.append(row)
                    if len(batch) == self.batch_size:
                        yield batch
                        batch = []
                yield batch
            else:
                continue_flag = False
            scan.close()
        card_check.close()
        print("finished iterator")

    async def announce_batch(self, batch_no, batch):
        out_data = {"type": "pair_request", "batch_no": batch_no}
        await self.redis_publish.rpush()
        await self.redis_publish.publish_json(self.publish_channel, out_data)

    async def listener_thread(self):
        async for msg in self.ch.iter(encoding="utf-8", decoder=json.loads):
            if msg["type"] == "pair_request":
                pairs = msg["data"]["pairs"]
                remove = await aioredis.create_redis(('localhost', 6379), password='foobared')
                await remove.srem(self.unprocessed_set, *pairs)
                remove.close()
            elif msg["type"] == "control":
                if msg["command"] == "shutdown":
                    break

    def start_listener(self):
        loop.run_until_complete(self.listener_thread())

    async def send_shutdown(self):
        await self.redis_publish.publish_json(self.publish_channel, {"type": "control", "command": "shutdown"})

    async def main(self):
        await self.pairs_to_redis()
        batch_no = 0
        async for batch in self.make_iterator():
            await self.announce_batch(batch_no, batch)
            print("announced batch", batch_no)
            batch_no += 1
            await asyncio.sleep(1)

if __name__ == "__main__":
    print("Started")

    m = Master()
    manager = aioprocessing.AioManager()

    # listener = aioprocessing.AioProcess(target=m.start_listener)
    # listener.start()
    m.load_sentences()
    sentence_dict = manager.dict()
    sentence_dict = m.sentences
    workers = []
    for i in range(3):
        workers.append(aioprocessing.AioProcess(target=init_worker, args=(sentence_dict, )))
        workers[-1].start()
    loop.run_until_complete(m.main())

# async def child_listen_worker(queue):
#     sub = await aioredis.create_redis(('localhost', 6379), password='foobared')
#     res = await sub.subscribe('task_created:1')
#     ch = res[0]
#     try:
#         while await ch.wait_message():
#             msg = await ch.get_json()
#             queue.put(msg)
#     except BrokenPipeError:
#         print("Child listen worker broken pipe")
#     finally:
#         sub.close()
#         await sub.wait_closed()
#     return
#
#
# def child_listen_thread(queue):
#     loop.run_until_complete(child_listen_worker(queue))
#
#
#
#
# async def parent_listen_worker(event, pair_maker, active_tasks, processed):
#     sub = await aioredis.create_redis(('localhost', 6379), password='foobared')
#     res = await sub.subscribe('task_completed:1')
#     ch = res[0]
#     while await ch.wait_message():
#         try:
#             msg = await ch.get_json()
#             if "shutdown" not in msg:
#                 pair_maker.receive_sims(msg['similarities'], processed)
#                 active_tasks.value -= 1
#                 event.set()
#             else:
#                 return
#         except BrokenPipeError:
#             # print("parent listen worker broken pipe")
#             sub.close()
#             await sub.wait_closed()
#             return
#
#
# def parent_listen_thread(event, pair_maker, active_tasks, processed):
#     loop.run_until_complete(parent_listen_worker(event, pair_maker, active_tasks, processed))
#
#
# async def go(event, pair_maker, active_tasks, unprocessed, processed):
#     pub = await aioredis.create_redis(('localhost', 6379), password='foobared')
#     batch_no = 0
#     for batch in pair_maker.make_iterator(unprocessed, processed):
#         out_data = {"algorithm_id": 1, "batch_no": batch_no, "pairs": batch}
#         try:
#             await pub.publish_json("task_created:1", out_data)
#         except asyncio.InvalidStateError:
#             print("go had invalid state")
#             await asyncio.sleep(3)
#         batch_no += 1
#         active_tasks.value += 1
#         if active_tasks.value >= 17 and len(unprocessed) > 0:
#             event.wait()
#             event.clear()
#     await pub.publish_json("task_created:1", {"shutdown": True})
#     pub.close()
#     await pub.wait_closed()
#     return

    # child_listener = aioprocessing.AioProcess(target=child_listen_thread, args=(task_queue,))
    # child_listener.start()
    #
    # for i in range(17):
    #     aioprocessing.AioProcess(target=calculate_thread, args=(task_queue, sentence_dict)).start()
    #
    # parent_listener = aioprocessing.AioProcess(target=parent_listen_thread, args=(event, pm, active_tasks, processed))
    # parent_listener.start()
    #
    # print("Start main loop")
    # loop.run_until_complete(go(event, pm, active_tasks, unprocessed, processed))
    # print("Ran until complete")
    #
    # manager.shutdown()
    # print("Done")
    # exit()
