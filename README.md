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
   $ pip install -r requirements.txt
   ```

   > Note: using `virtualenv` is preferred.

1. Run the code:

   ```
   $ python simulation.py
   ```
