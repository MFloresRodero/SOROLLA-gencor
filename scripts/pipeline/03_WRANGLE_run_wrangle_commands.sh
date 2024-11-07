#!/bin/bash
commands_dir="/gpfs/projects/bsc02/mflores/gencor/SumStats/Wrangled/commands"
for cmd_file in "$commands_dir"/*.sh
do
  bash "$cmd_file"
done
