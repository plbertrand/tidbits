#!/bin/bash
systemctl --user stop timemachine
mkdir -p $HOME/.config/systemd/user
cp timemachine.service $HOME/.config/systemd/user/timemachine.service
systemctl --user daemon-reload
systemctl --user enable timemachine
./run.sh
systemctl --user restart timemachine

