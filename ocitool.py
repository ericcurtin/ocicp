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

def sha256sum(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for b in iter(lambda: f.read(4096), b''):
            h.update(b)

    return h.hexdigest()

def run_cmd(cmd, check=True):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(result.returncode)

    return result.stdout.strip()

def make_dir_image(files, tempdir):
    # 1. Create a layer tarball from the given files.
    layer_tar_path = os.path.join(tempdir, "layer.tar")
    with tarfile.open(layer_tar_path, "w") as tar:
        for f in files:
            tar.add(f, arcname=os.path.basename(f))
    layer_digest_hex = sha256sum(layer_tar_path)
    layer_digest = "sha256:" + layer_digest_hex
    layer_size = os.path.getsize(layer_tar_path)

    # Skopeo expects the file to be named as the hex digest, no extension.
    final_layer_path = os.path.join(tempdir, layer_digest_hex)
    shutil.move(layer_tar_path, final_layer_path)

    # 2. Create a minimal config (Docker image config, V2 Schema 2)
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

    # 3. Write manifest as an OBJECT (not an array)
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
                "mediaType": "application/vnd.docker.image.rootfs.diff.tar",
                "size": layer_size,
                "digest": layer_digest
            }
        ]
    }
    manifest_json = os.path.join(tempdir, "manifest.json")
    with open(manifest_json, "w") as f:
        json.dump(manifest, f, separators=(",", ":"))

def push(image_ref, files):
    with tempfile.TemporaryDirectory() as tempdir:
        make_dir_image(files, tempdir)
        run_cmd([
            "skopeo", "copy",
            f"dir:{tempdir}",
            f"docker://{image_ref}"
        ])
        print(f"Pushed {image_ref} with files: {', '.join(files)}")

def pull(image_ref):
    with tempfile.TemporaryDirectory() as tempdir:
        run_cmd([
            "skopeo", "copy",
            f"docker://{image_ref}",
            f"dir:{tempdir}"
        ])
        manifest_json = os.path.join(tempdir, "manifest.json")
        with open(manifest_json) as f:
            manifest = json.load(f)
        for layer in manifest["layers"]:
            layer_digest = layer["digest"].split(":")[1]
            layer_tar = os.path.join(tempdir, layer_digest)
            if os.path.exists(layer_tar):
                with tarfile.open(layer_tar, "r") as tarf:
                    tarf.extractall(".")
                    print(f"Extracted files from layer {layer_digest}")

        print(f"Pulled and extracted files from {image_ref}")

def main():
    parser = argparse.ArgumentParser(description="Simple OCI registry file push/pull tool using skopeo.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    push_parser = subparsers.add_parser("push", help="Push files to OCI image")
    push_parser.add_argument("image", help="OCI image reference (e.g. quay.io/repo/image)")
    push_parser.add_argument("files", nargs="+", help="Files to push")

    pull_parser = subparsers.add_parser("pull", help="Pull files from OCI image")
    pull_parser.add_argument("image", help="OCI image reference (e.g. quay.io/repo/image)")

    args = parser.parse_args()
    if args.command == "push":
        push(args.image, args.files)
    elif args.command == "pull":
        pull(args.image)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

