"""

Command Line Interface for Reflection Tools:
====================================

.. currentmodule:: reflection

class methods:

   fetch_from_cache

"""

import argparse
import datetime
import pickle
import os
import sys
import re
import hashlib

from tqdm import tqdm
import numpy as np
import pandas as pd
from itertools import chain



class Cache:

    """
    Checks if the results are in a pickle file if it is then it return otherwise
    returns None

    """

    @staticmethod
    def get_it_from_cache(
        content, pickle_folder='/tmp/', prefix="google-ocr"
    ):
        """read it from cache file"""

        data = None
        cache_filename = (
            pickle_folder + "/"
            + hashlib.md5(content).hexdigest()
            + "-{}.pickle".format(prefix)
        )
        if os.path.exists(cache_filename):
            print("Reading from {}".format(cache_filename))
            with open(cache_filename, "rb") as f:
                data = pickle.load(f)

        return data

    @staticmethod
    def save_it_to_cache(
        data,
        content,
        pickle_folder='/tmp/',
        prefix="google-ocr",
        protocol=pickle.HIGHEST_PROTOCOL
    ):
        """save it to the cache file"""

        cache_filename = (
            pickle_folder + "/"
            + hashlib.md5(content).hexdigest()
            + "-{}.pickle".format(prefix)
        )
        with open(cache_filename, "wb") as f:
            print("Saving to {}".format(cache_filename))
            pickle.dump(data, f, protocol=protocol)
            return True

        return False
