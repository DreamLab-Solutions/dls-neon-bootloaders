#!/usr/bin/env python3
"""Prepare and publish a locally validated boot theme release bundle."""

import argparse
import base64
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.request

from release import REPO, ROOT, asset_names


FEED = "https://nexus.sunnyday.software/repository/dreamlab-artifacts/sha256/"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def release_source() -> dict:
    version = (ROOT / "VERSION").read_text().strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("Set VERSION to the reviewed stable source version")
    if git("status", "--porcelain"):
        raise ValueError("Use a clean checkout of the reviewed release tag")
    commit = git("rev-parse", "HEAD")
    tag = "v" + version
    ref = "refs/tags/" + tag
    refs = {
        name: object_id
        for object_id, name in (line.split() for line in git("ls-remote", REPO, ref, ref + "^{}").splitlines())
    }
    if git("rev-parse", ref + "^{commit}") != commit or refs.get(ref + "^{}", refs.get(ref)) != commit:
        raise ValueError("The local checkout and canonical release tag must identify the same commit")
    return {"version": version, "tag": tag, "sourceRepository": REPO, "sourceCommit": commit}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def release_checksums(files: dict[str, bytes], version: str) -> bytes:
    return "".join(f"{sha256(files[name])}  {name}\n" for name in asset_names(version)).encode()


def build_bundle(stage: Path, source: dict) -> bytes:
    version = source["version"]
    names = [*asset_names(version), "SHA256SUMS", "RELEASE-NOTES.md"]
    files = {name: (stage / name).read_bytes() for name in names}
    if files["SHA256SUMS"] != release_checksums(files, version):
        raise ValueError("The staged packages differ from their SHA256SUMS file")
    files["SOURCE.json"] = (json.dumps(source, sort_keys=True) + "\n").encode()
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as bundle:
            for name, content in files.items():
                member = tarfile.TarInfo(name)
                member.mode, member.size = 0o644, len(content)
                bundle.addfile(member, io.BytesIO(content))
    return output.getvalue()


def verify_bundle(payload: bytes, source: dict) -> None:
    names = [*asset_names(source["version"]), "SHA256SUMS", "RELEASE-NOTES.md", "SOURCE.json"]
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as bundle:
        entries = bundle.getmembers()
        if any(not member.isfile() for member in entries) or sorted(member.name for member in entries) != sorted(names):
            raise ValueError("The Nexus bundle must contain exactly the staged release files and source metadata")
        files = {member.name: bundle.extractfile(member).read() for member in entries}
    if json.loads(files["SOURCE.json"]) != source or files["SHA256SUMS"] != release_checksums(files, source["version"]):
        raise ValueError("The Nexus bundle differs from the canonical source or its package checksums")


def authorization() -> str:
    token = os.environ.get("DREAMLAB_NEXUS_AUTH")
    if not token:
        config_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "dreamlab/artifacts"
        config = Path(os.environ.get("DREAMLAB_NEXUS_CONFIG", config_dir / "nexus.json"))
        if config.stat().st_mode & 0o077:
            raise ValueError("Nexus credential file must be private")
        credentials = json.loads(config.read_text())
        if credentials.get("rawBaseUrl") != FEED:
            raise ValueError("The configured Nexus feed differs from the canonical DreamLab artifact feed")
        token = credentials["basicAuth"]
    if not isinstance(token, str) or b":" not in base64.b64decode(token, validate=True):
        raise ValueError("The Nexus Basic credential is invalid")
    return "Basic " + token


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        raise ValueError("Nexus redirected the request")


def transfer(digest: str, auth: str, size: int):
    url = FEED + digest + ".tgz"
    client = urllib.request.build_opener(NoRedirect)

    def request(payload: bytes | None = None) -> bytes | None:
        method = "GET" if payload is None else "PUT"
        headers = {"Authorization": auth}
        if payload is not None:
            headers["Content-Type"] = "application/gzip"
            headers["If-None-Match"] = "*"
        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with client.open(req, timeout=120) as response:
                return response.read(size + 1) if payload is None else b""
        except urllib.error.HTTPError as error:
            if payload is None and error.code == 404:
                return None
            raise ValueError(f"Nexus {method} returned HTTP {error.code}") from None

    return request


def publish(payload: bytes, request) -> str:
    existing = request()
    if existing is not None:
        if existing != payload:
            raise ValueError("The Nexus digest URL contains different bytes")
        return "already-present"
    try:
        request(payload)
    except (ValueError, OSError):
        if request() == payload:
            return "already-present"
        raise
    if request() != payload:
        raise ValueError("Nexus readback differs from the bundle")
    return "published"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", type=Path, metavar="BUNDLE", help="publish this prepared bundle to Nexus")
    args = parser.parse_args()
    source = release_source()
    if args.publish:
        payload = args.publish.read_bytes()
        verify_bundle(payload, source)
        digest = sha256(payload)
        if args.publish.name != digest + ".tgz":
            raise ValueError("The prepared bundle filename differs from its SHA-256")
        status = publish(payload, transfer(digest, authorization(), len(payload)))
        path = args.publish
    else:
        build_env = {key: value for key, value in os.environ.items() if not key.startswith("DREAMLAB_NEXUS_")}
        subprocess.run(["bash", "scripts/validate-local.sh"], cwd=ROOT, env=build_env, check=True)
        if release_source() != source:
            raise ValueError("The release source changed during validation")
        payload = build_bundle(ROOT / "dist/release", source)
        digest = sha256(payload)
        output = ROOT / "dist/nexus"
        output.mkdir(exist_ok=True)
        path = output / (digest + ".tgz")
        with tempfile.NamedTemporaryFile(dir=output) as temporary:
            temporary.write(payload)
            temporary.flush()
            try:
                os.link(temporary.name, path)
            except FileExistsError:
                if path.read_bytes() != payload:
                    raise ValueError("The existing local bundle differs from the prepared bytes") from None
        status = "prepared"
    print(json.dumps(dict(source, status=status, path=str(path), url=FEED + digest + ".tgz", sha256=digest, size=len(payload))))


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError, tarfile.TarError) as error:
        raise SystemExit(str(error)) from None
