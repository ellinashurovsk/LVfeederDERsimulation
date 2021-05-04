#!/bin/bash

WORKER_PID=''

handle_sig_term() {
  echo "* SIGTERM received, informing python script"
  kill -TERM $WORKER_PID
  wait $WORKER_PID
}

handle_sig_int() {
  echo "* SIGINT received, informing python script"
  kill -INT $WORKER_PID
  wait $WORKER_PID
}

trap 'handle_sig_int' INT
trap 'handle_sig_term' TERM

I=0

echo "* Starting python script"
python3 -u simulation.py & WORKER_PID=$!
wait $WORKER_PID
