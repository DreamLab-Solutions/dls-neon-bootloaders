#!/usr/bin/env python3
"""Check publication content without printing matched private values."""
import argparse
from pathlib import Path, PurePosixPath
import re
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PATTERNS={
    'private conversation URL': re.compile(rb'https?://(?:www\.)?chatgpt\.com/c/[0-9a-f-]{20,}',re.I),
    'named local home path': re.compile(rb'/home/[A-Za-z0-9_.-]+/'),
    'private key': re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'credential token': re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16})'),
}


def findings(name,data):
    result=[]
    path=PurePosixPath(name)
    if 'reference' in path.parts or path.name in {'.env','id_rsa','id_ed25519'} or path.suffix.lower() in {'.pem','.p12','.kdbx'}:
        result.append('private/reference file')
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        pos=8
        while pos+12<=len(data):
            length=struct.unpack('>I',data[pos:pos+4])[0]
            kind=data[pos+4:pos+8]
            if pos+12+length>len(data):
                result.append('invalid PNG');break
            if kind in {b'tEXt',b'iTXt',b'zTXt',b'eXIf'}:result.append('PNG metadata')
            pos+=12+length
            if kind==b'IEND':
                if pos!=len(data):result.append('PNG trailing data')
                break
    elif b'\0' not in data[:8192]:
        result += [label for label,pattern in PATTERNS.items() if pattern.search(data)]
    return result


def check_files(files):
    bad=[f'{name}: {", ".join(found)}' for name,data in files.items() if (found:=findings(name,data))]
    if bad:raise RuntimeError('Publication privacy check failed:\n'+'\n'.join(bad))


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history',action='store_true')
    args=parser.parse_args()
    if args.history:
        files={}
        for entry in git('rev-list','--objects','--all').decode().splitlines():
            sha,_,name=entry.partition(' ')
            if name and git('cat-file','-t',sha).strip()==b'blob':files[f'{sha}:{name}']=git('cat-file','blob',sha)
    else:
        files={name:(ROOT/name).read_bytes() for name in git('ls-files','-z').decode().split('\0') if name and (ROOT/name).is_file()}
    check_files(files)
    print(f'Publication privacy check: {len(files)} files/blobs OK; matched values never printed')


if __name__=='__main__':main()
