import h5py as h5
from functools import partial
from mpi4py import MPI
from py.mi_algorithm import MihalceaSentSimBNC

mi = MihalceaSentSimBNC()

parent_comm = MPI.Comm.Get_parent().Merge()
world_comm = MPI.COMM_WORLD
rank = parent_comm.Get_rank()
size = parent_comm.Get_size()
fn = parent_comm.bcast(None, root=0)
announcer = parent_comm.bcast(None, root=0)
announcer = partial(announcer, process="Worker-{}".format(rank))
f = h5.File(fn, 'a', driver='mpio', comm=world_comm)

sentence_ds = f['/input/tokenized_text']
sentences = [s.split() for s in sentence_ds]
sims = f['/sim/mi']

sentence_count = len(sentences)

try:
    for left_index in range(rank, sentence_count, size):
        new_sims = []
        for right_index in range(left_index, sentence_count):
            new_sims.append(mi.similarity(sentences[left_index], sentences[right_index]))
        sims[left_index, left_index:] = new_sims
        if left_index % 100 == 0:
            announcer("finished row {:>6,d}/{:>6,d}".format(left_index, sentence_count))
            f.flush()
finally:
    f.flush()
    f.close()

parent_comm.Disconnect()