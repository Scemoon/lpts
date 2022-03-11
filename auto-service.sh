#!/bin/bash
cp -rvf node.service /etc/systemd/system/node.service
systemctl daemon-reload
systemctl enable node.service

