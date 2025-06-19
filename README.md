# ocicp

A command-line utility for pushing and pulling files to and from OCI-compatible registries using [skopeo](https://github.com/containers/skopeo). This tool packages one or more files as an OCI image layer and uploads or downloads them directly from a registry.

## Install

```
curl -fsSL https://raw.githubusercontent.com/ericcurtin/ocicp/refs/heads/main/install.sh | sudo bash
```

## Features

- **Push** files as a single-layer OCI image to any registry supported by `skopeo`.
- **Pull** and extract files from a single-layer OCI image in a registry.
- Only requires `skopeo` and `python3`.

## Usage

```
ocicp push <image> <file1> [<file2> ...]
ocicp pull <image>
```

### Examples

#### Push files to a registry

```
$ ocicp push quay.io/yourorg/yourimage:latest file1.txt file2.conf
Getting image source signatures
Copying blob 6c43a1ee1e9b done   |
Copying config eeab4a7bd2 done   |
Writing manifest to image destination
```

- Packages `file1.txt` and `file2.conf` into a single-layer OCI image and pushes it.

#### Pull files from a registry

```
$ ocicp pull quay.io/yourorg/yourimage:latest
Getting image source signatures
Copying blob 6c43a1ee1e9b done   |
Copying config eeab4a7bd2 done   |
Writing manifest to image destination
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

- If pushing to a private registry, make sure you've logged in using `skopeo login`.

