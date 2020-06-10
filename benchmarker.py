import numpy as np
import time

class benchmark(object):

    def __init__(self, form):


        start_time = time.time()

        for i in range(10):
            np.random.seed(i)
            arr = np.random.rand(1000, 1000)
            arr_copy = np.copy(arr)
            arr_copy = arr**2
            arr**=2

        end_time = time.time()

        form.showError("Benchmarking time " + str(end_time - start_time))