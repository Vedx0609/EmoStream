#!/bin/bash

# List of all files that we are executing (Entire pub-sub architecture)
all_files=("main_pub_cluster1.py" "main_pub_cluster2.py" "main_subscriber1.py" "main_subscriber2.py" "main_subscriber3.py" "main_subscriber4.py")

# Fancy echo function for status messages
fancy_echo() {
    echo -e "\033[1;32m[INFO]\033[0m $1"
}

fancy_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

fancy_divider() {
    echo -e "\033[1;34m----------------------------------------\033[0m"
}

# Running all files
for single_file in "${all_files[@]}"; do
    fancy_echo "Starting $single_file..."
    
    # Execute python file in the background
    python "$single_file" &
    
    # Capture the PID of the background process
    pid=$!
    fancy_echo "$single_file started with PID $pid."
    
    fancy_divider
done

# Wait for all background processes to complete
wait

fancy_echo "All files executed!"
