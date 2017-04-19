from functools import partial
from itertools import combinations, islice, count, zip_longest
from os import getenv, mkdir
from shutil import rmtree
from datetime import datetime

import subprocess

from py.algorithm import clean_string
import py.worker as w
import multiprocessing as mp

filename = getenv("TARGET", "variable_definition")


def echo_message(msg, process, start, ):
    print("{:<20}{:<20}{:<39}".format(process, str(datetime.now()-start), msg))


class MiSim(object):

    def __init__(self):
        self.sentences = dict()
        self.batch_count = 0
        self.announcer = partial(echo_message, process="MiSim", start=datetime.now())

    def load_sentences(self):
        with open("/app/data/%s.txt" % filename) as in_file:
            in_file.readline()
            raw_sentences = {x[0]: x[1] for x in [l.split("\t") for l in in_file.readlines()]}
        self.announcer("load sentences")
        self.sentences = {k: clean_string(v) for k, v in raw_sentences.items()}
        self.announcer("cleaned sentences")
        return self.sentences

    def create_temp_dir(self):
        try:
            rmtree("/app/data/temp_sim")
        except FileNotFoundError:
            pass
        mkdir("/app/data/temp_sim")
        self.announcer("made temp_dir")

    def create_batch(self):
        pairs = combinations(self.sentences, 2)
        batch_size = 1000
        batch_count = len(self.sentences)*(len(self.sentences)-1)//2
        for batch_no, batch in zip(count(), zip_longest(*[iter(pairs)]*batch_size, fillvalue=None)):
            yield batch_no, batch

    def calculate_similarities(self):
        self.announcer("made pairs")
        with mp.Pool(19, initializer=w.init_worker, initargs=(self.sentences, self.announcer)) as pool:
            pool.starmap_async(w.process_batch, self.create_batch(), chunksize=100).get()
        self.announcer("calculated similarities")

    def merge_similarity_files(self):
        subprocess.run("cat /app/data/temp_sim/sims-*.csv > /app/data/output/%s_Mi.csv" % filename, shell=True)
        self.announcer(msg="Catted all files to sims.csv")
        rmtree("/app/data/temp_sim")
        self.announcer(msg="Removed temp_sims")

    def main(self):
        self.load_sentences()
        self.create_batch()
        self.create_temp_dir()
        self.calculate_similarities()

if __name__ == "__main__":
    m = MiSim()
    m.main()


    # async def pairs_to_redis(self):
    #     pairs = ["%s_%s" % (p[0], p[1]) for p in combinations(self.sentences.keys(), 2)]
    #     print("made pairs")
    #     conn = await aioredis.create_redis(('localhost', 6379), password='foobared', encoding="utf-8")
    #     self.batch_count = math.ceil(len(pairs)/self.batch_size)
    #     for i in range(math.ceil(self.batch_count/100)):
    #         pair_batch = pairs[i*self.batch_size*100:(i+1)*self.batch_size*100]
    #         conn.sadd(self.unprocessed, *pair_batch)
    #         print("added batch %d/%d" % (i, self.batch_count/100))
    #     conn.close()
    #     print("sent pairs to redis")
    #
    # async def get_results(self):
    #     redis = await aioredis.create_redis(('localhost', 6379), password='foobared', encoding="utf-8")
    #     row_count = 0
    #     with open("/app/data/%s.csv" % filename, "w") as o:
    #         for left in self.sentences:
    #             key = "sim_%s" % left
    #             async for right, sim in redis.ihscan(key):
    #                 row_count += 1
    #                 o.write("%s,%s,%0.4f\n" % (left, right, float(sim)))
    #     print("wrote rows", row_count)
#
# if __name__ == "__main__":
#     m = Master()
#     m.load_sentences()
#     with mp.Pool(self._cfg.num_cores, initializer=sbw.init_worker, initargs=(self._cfg, self.announcer,
#                                                                              batch_count, self.r)) as pool:
#         pool.starmap_async(sbw.process_batch,
#                            [(b[0], b[1], c) for b, c in zip(batches, count(start=1))],
#                            chunksize=10).get()
#     workers = []
#     for i in range(cpu_count() - 1):
#         workers.append(aioprocessing.AioProcess(target=init_worker, args=(sentence_dict, batch_no, m.batch_count)))
#         workers[-1].start()
#     print("workers created")
#     for w in workers:
#         w.join()
#
#     loop.run_until_complete(m.get_results())
