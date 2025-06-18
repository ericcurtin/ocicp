# ocitool.py

A minimal command-line utility for pushing and pulling files to and from OCI-compatible registries using [skopeo](https://github.com/containers/skopeo). This tool packages one or more files as a Docker-compatible OCI image layer and uploads or downloads them directly from a registry.

## Features

- **Push** files as a single-layer OCI image to any registry supported by `skopeo`.
- **Pull** and extract files from a single-layer OCI image in a registry.
- Only requires `skopeo` and `python3`.

## Usage

```sh
./ocitool.py push <image> <file1> [<file2> ...]
./ocitool.py pull <image>
```

### Examples

#### Push files to a registry

```sh
./ocitool.py push quay.io/yourorg/yourimage:latest file1.txt file2.conf
```

- Packages `file1.txt` and `file2.conf` into a single-layer OCI image and pushes it to `quay.io/yourorg/yourimage:latest`.

#### Pull files from a registry

```sh
./ocitool.py pull quay.io/yourorg/yourimage:latest
```

- Downloads the OCI image and extracts its files into the current directory.

## Requirements

- Python 3.6 or later
- [skopeo](https://github.com/containers/skopeo) must be installed and available in your `$PATH`

## How it works

1. **Push:**
   - Creates a layer tarball containing the specified files.
   - Generates a minimal OCI image config and manifest.
   - Uploads the local directory image to the specified registry reference.

2. **Pull:**
   - Download the image from the registry into a local temp directory.
   - Extracts the files from the image layer into the working directory.

## Design Notes

- Images are created using Docker V2 Schema 2 (OCI compatible).
- Each push creates a new image with a single layer containing the provided files.
- Files are always extracted into the current directory on pull.
- Layer and config files are named by their SHA256 digest to comply with `skopeo` expectations.

## Limitations (for now)

- Only supports single-layer images (all files are packed together).
- No support for advanced image features (labels, commands, environment, etc.).
- No authentication handling—ensure `skopeo` is configured for your registry.

## Troubleshooting

- If you encounter errors, ensure `skopeo` is installed and can access your registry.
- If pushing to a private registry, make sure you've logged in using `podman login` or have the correct credentials set up.

