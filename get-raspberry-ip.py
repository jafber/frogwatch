#!/bin/python

from requests import get

ip = get('https://gist.githubusercontent.com/CheeseCrustery/a80945ec5a6d0dfa8e067b0f9849d71c/raw/ipv4.txt').text.strip()
print(ip)
hosts = '/etc/hosts'
try:
    with open(hosts, 'r') as f:
        lines = f.readlines()
    for i in range(len(lines)):
        if 'raspberry' in lines[i]:
            lines[i] = f'{ip}\traspberry\n'
            break
    with open(hosts, 'w') as f:
        f.writelines(lines)
except:
    pass
