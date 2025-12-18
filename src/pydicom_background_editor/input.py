"""
Module to handle reading of Storable data from stdin.

It has to handle situations where it may take a few seconds for data
to be ready, and most importantly it needs to be able to read bytes
from stdin without blocking, because the calling script will not close
stdout when it is finished.

There might be better ways to do this, or other improvements to be had.
"""
import os
import sys
import select
from storable.core import thaw
from storable.output import serialize

TIMEOUT = 15  # seconds

def get_input_data() -> None:
    fd = sys.stdin.fileno()

    ready, _, _ = select.select([fd], [], [], TIMEOUT)

    if not ready:
        raise TimeoutError(f"No input received within {TIMEOUT} seconds.")

    # read binary data from stdin
    # TODO: might need to use os.read(fd, n) instead, where n is a max size
    # input_data = sys.stdin.read()

    input_data = os.read(fd, 10**7)  # read up to 10 MB

    # deserialize using storable
    data = thaw(input_data[4:])  # skip first 4 bytes (storable header)

    return data

def respond_error():
    results = {}

    results['Status'] = 'Error'
    results['message'] = 'no data was read'

    encoded = serialize(results)
    sys.stdout.buffer.write(encoded)

def respond_ok(tdata):
    results = {}

    ## an success
    results['Status'] = 'OK'
    results['from_file'] = tdata['from_file']
    results['to_file'] = tdata['to_file']

    encoded = serialize(results)
    sys.stdout.buffer.write(encoded)