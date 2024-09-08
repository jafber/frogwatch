#!/bin/python

from requests import get

# DEPRECATED, USE SSHPI INSTEAD
# make 'raspberry' dns entry in /etc/hosts
# ssh pi@raspberry
ip = get('https://gist.githubusercontent.com/jafber/a80945ec5a6d0dfa8e067b0f9849d71c/raw/ipv4.txt').text.strip()
print(ip)
hosts = '/etc/hosts'
try:
    with open(hosts, 'r') as f:
        lines = f.readlines()
    wrote = False
    for i in range(len(lines)):
        if 'raspberry' in lines[i]:
            print('writing ip to /etc/hosts')
            lines[i] = f'{ip}\traspberry\n'
            break
    if not wrote:
        print('writing ip to /etc/hosts')
        lines.append(f'{ip}\traspberry')
    with open(hosts, 'w') as f:
        f.writelines(lines)
except Exception as e:
    print(e)
