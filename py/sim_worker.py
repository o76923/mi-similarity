import h5py as h5
from functools import partial
from mpi4py import MPI
from py.mi_algorithm import MiSim

parent_comm = MPI.Comm.Get_parent().Merge()
world_comm = MPI.COMM_WORLD
rank = parent_comm.Get_rank()
size = parent_comm.Get_size()

announcer = parent_comm.bcast(None, root=0)
announcer = partial(announcer, process="Worker-{}".format(rank))

file_name = parent_comm.bcast(None, root=0)
f = h5.File(file_name, 'a', driver='mpio', comm=world_comm)
if rank == 1:
    announcer('Loaded File')

sims = f['/sim/mi']
sentence_ds = f['/input/tokenized_text']
sentences = [s.split() for s in sentence_ds]
if rank == 1:
    announcer('tokenized sentences')

sim_algorithms = parent_comm.bcast(None, root=0)
mi = MiSim(sim_algorithms)
if rank == 1:
    announcer('initialized mi')
sentence_count = len(sentences)

try:
    for left_index in range(rank-1, sentence_count, size-1):
        new_sims = []
        for right_index in range(left_index, sentence_count):
            new_sims.append(mi.similarity(sentences[left_index], sentences[right_index]))
        # with sims.collective:
        sims[left_index, left_index:] = new_sims
        f.flush()
        announcer("finished row {:>6,d}/{:>6,d}".format(left_index, sentence_count))
finally:
    f.flush()
    f.close()
announcer("Worker finished")
parent_comm.Disconnect()