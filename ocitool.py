#!/usr/bin/env python3

import argparse
import subprocess
import sys
import tempfile
import os
import tarfile
import hashlib
import json
import time
import shutil
import gzip

def sha256sum(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for b in iter(lambda: f.read(4096), b''):
            h.update(b)
    return h.hexdigest()

def run_cmd(cmd, check=True):
    result = subprocess.run(cmd)
    if check and result.returncode != 0:
        return result.returncode
    return 0

def create_layer_tarball(files, tempdir):
    """1. Create a layer tarball from the given files as a gzip-compressed tar with max compression."""
    layer_tar_path = os.path.join(tempdir, "layer.tar.gz")
    # Use tarfile to write to an uncompressed tar, then gzip manually with max compression
    raw_tar_path = os.path.join(tempdir, "layer-raw.tar")
    with tarfile.open(raw_tar_path, "w") as tar:
        for f in files:
            tar.add(f, arcname=os.path.basename(f))
    # Gzip with maximum compression
    with open(raw_tar_path, "rb") as f_in, gzip.open(layer_tar_path, "wb", compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)
    os.remove(raw_tar_path)
    # Digest is over the *compressed* tar
    layer_digest_hex = sha256sum(layer_tar_path)
    layer_digest = "sha256:" + layer_digest_hex
    layer_size = os.path.getsize(layer_tar_path)
    # Skopeo expects the file to be named as the hex digest, no extension.
    final_layer_path = os.path.join(tempdir, layer_digest_hex)
    shutil.move(layer_tar_path, final_layer_path)
    return layer_digest, layer_digest_hex, layer_size, final_layer_path

def create_config(layer_digest, tempdir):
    """2. Create a minimal config (Docker image config, V2 Schema 2)."""
    created = time.strftime("%Y-%m-%dT%H:%M:%S.000000000Z", time.gmtime())
    config = {
        "created": created,
        "architecture": "amd64",
        "os": "linux",
        "config": {},
        "rootfs": {
            "type": "layers",
            "diff_ids": [layer_digest]
        },
        "history": [{
            "created": created,
            "created_by": "ocitool.py"
        }]
    }
    config_json_path = os.path.join(tempdir, "config.json")
    with open(config_json_path, "w") as f:
        json.dump(config, f, separators=(",", ":"))
    config_digest_hex = sha256sum(config_json_path)
    config_digest = "sha256:" + config_digest_hex
    config_size = os.path.getsize(config_json_path)
    # Name config as its digest too
    final_config_path = os.path.join(tempdir, config_digest_hex)
    shutil.move(config_json_path, final_config_path)
    return config_digest, config_digest_hex, config_size, final_config_path

def write_manifest_object(config_digest, config_size, layer_digest, layer_size, tempdir):
    """3. Write manifest as an OBJECT (not an array)."""
    manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": config_size,
            "digest": config_digest
        },
        "layers": [
            {
                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                "size": layer_size,
                "digest": layer_digest
            }
        ]
    }
    manifest_json = os.path.join(tempdir, "manifest.json")
    with open(manifest_json, "w") as f:
        json.dump(manifest, f, separators=(",", ":"))
    return manifest_json

def make_dir_image(files, tempdir):
    layer_digest, layer_digest_hex, layer_size, final_layer_path = create_layer_tarball(files, tempdir)
    config_digest, config_digest_hex, config_size, final_config_path = create_config(layer_digest, tempdir)
    manifest_json = write_manifest_object(config_digest, config_size, layer_digest, layer_size, tempdir)
    return {
        "layer": final_layer_path,
        "config": final_config_path,
        "manifest": manifest_json
    }

def push(image_ref, files):
    with tempfile.TemporaryDirectory() as tempdir:
        make_dir_image(files, tempdir)
        ret = run_cmd([
            "skopeo", "copy",
            f"dir:{tempdir}",
            f"docker://{image_ref}"
        ])
        if ret:
           return ret

        print(f"Pushed files to {image_ref}")

        return 0

def pull(image_ref):
    with tempfile.TemporaryDirectory() as tempdir:
        ret = run_cmd([
            "skopeo", "copy",
            f"docker://{image_ref}",
            f"dir:{tempdir}"
        ])
        if ret:
           return ret

        manifest_json = os.path.join(tempdir, "manifest.json")
        with open(manifest_json) as f:
            manifest = json.load(f)
        for layer in manifest["layers"]:
            layer_digest = layer["digest"].split(":")[1]
            layer_tar = os.path.join(tempdir, layer_digest)
            if os.path.exists(layer_tar):
                # extract gzip-compressed tar layer
                with gzip.open(layer_tar, "rb") as gzfile:
                    with tarfile.open(fileobj=gzfile, mode="r:") as tarf:
                        tarf.extractall(".", filter="data")

        print(f"Pulled files from {image_ref}")

        return 0

def main():
    parser = argparse.ArgumentParser(description="Simple OCI registry file push/pull tool using skopeo.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    push_parser = subparsers.add_parser("push", help="Push files to OCI image")
    push_parser.add_argument("image", help="OCI image reference (e.g. quay.io/repo/image)")
    push_parser.add_argument("file", nargs="+", help="Files to push")

    pull_parser = subparsers.add_parser("pull", help="Pull files from OCI image")
    pull_parser.add_argument("image", help="OCI image reference (e.g. quay.io/repo/image)")

    args = parser.parse_args()
    ret = 0
    if args.command == "push":
        ret = push(args.image, args.file)
    elif args.command == "pull":
        ret = pull(args.image)
    else:
        parser.print_help()

    sys.exit(ret)

if __name__ == "__main__":
    main()

