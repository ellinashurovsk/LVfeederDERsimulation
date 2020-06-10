## Running the code

There are two options available if you'd like to run the simulation yourself:

1. Run the code via Docker (preferred)
1. Run the code directly

### Running the code via Docker

If you are on Linux or MacOS, issue the following command to build and run the Docker image:

```
$ ./run.sh
```

If you are on Windows, you should probably be using WSL with some distribution of Linux inside.

### Running the code directly

#### Required dependencies

1. Python 3.x (tested on 3.8.3 64-bit) - check https://python.org for the suitable installation guide.
1. _You might also need to install a compiler toolchain for your OS. See https://python.org._
1. Install dependencies by issuing the following command:

   ```
   $ pip install numba==0.49.1 pandas==1.0.4 cvxpy==1.0.31
   ```

   > Note: you might need to install `wheel` first (`$ pip install wheel`).

1. Install specific version of `pandapower` by issuing the following command:

   ```
   $ pip install git+https://github.com/lthurner/pandapower.git@1e6f29d632a31acf437d094b69edcefc048dbcfe
   ```

   > Note: `1e6f29d632a31acf437d094b69edcefc048dbcfe` is the latest commit on branch `develop` as of 2020.06.09. You may try the latest commit (as of now) instead, but it is not guaranteed to work.

1. Run the code:

   ```
   $ python simulation.py
   ```
