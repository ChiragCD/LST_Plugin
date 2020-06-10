import numpy as np
import time

class benchmark(object):

    def __init__(self, form):

        np.random.seed(0)

        start_time = time.time()

        arr = np.random.rand(100, 100)
        print(arr)
        arr_copy = np.copy(arr)
        arr_copy = arr**2
        arr**=2

        end_time = time.time()

        form.showError(start_time - end_time)