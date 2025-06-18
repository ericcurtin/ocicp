# ocicp

A minimal command-line utility for pushing and pulling files to and from OCI-compatible registries using [skopeo](https://github.com/containers/skopeo). This tool packages one or more files as an OCI image layer and uploads or downloads them directly from a registry.

## Install

```
curl -fsSL https://raw.githubusercontent.com/ericcurtin/ocicp/refs/heads/main/install.sh | sudo bash
```

## Features

- **Push** files as a single-layer OCI image to any registry supported by `skopeo`.
- **Pull** and extract files from a single-layer OCI image in a registry.
- Only requires `skopeo` and `python3`.

## Usage

```sh
ocicp push <image> <file1> [<file2> ...]
ocicp pull <image>
```

### Examples

#### Push files to a registry

```sh
ocicp push quay.io/yourorg/yourimage:latest file1.txt file2.conf
```

- Packages `file1.txt` and `file2.conf` into a single-layer OCI image and pushes it to `quay.io/yourorg/yourimage:latest`.

#### Pull files from a registry

```sh
ocicp pull quay.io/yourorg/yourimage:latest
```

- Downloads the OCI image and extracts its files into the current directory.

## Requirements

- Python 3.9 or later
- [skopeo](https://github.com/containers/skopeo) must be available

## Design Notes

- Images are created using Image Manifest Version 2, Schema 2 (OCI compatible).
- Each push creates a new image with a single layer containing the provided files.
- Layer and config files are named by their SHA256 digest to comply with `skopeo` expectations.

## Troubleshooting

- If pushing to a private registry, make sure you've logged in using `podman login` or have the correct credentials set up.

