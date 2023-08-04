# sops-run
A python wrapper for [sops](https://github.com/getsops/sops) to execute commands with environment variables decrypted from a sops encrypted file.

```bash
usage: sops-run [-h] [--create] [--edit] [--key KEY] command [command ...]

Run a command with secrets decrypted from sops files.

positional arguments:
  command     Command to run

options:
  -h, --help  show this help message and exit
  --create    Create a new sops-run manifest
  --edit      Edit a sops-run manifest
  --key KEY   Path to age key to use for encryption/decryption
```

## Overview
I frequently come across times when I want to run a command that has secrets provided via environment files. However, I didn't really like the concept of storing secrets in my user profile, loaded into my shell environment and readable by any process I run. I remembered hearing about [sops](https://github.com/getsops/sops) and did a little digging. Turns out it supports this exact use case with the argument `exec-env`, however I didn't want to remember the path to the sops file and the command to run every time I wanted to run a command. This wrapper addresses that. 

## Installation and setup
### Requirements
- python3 (tested against python 3.11)
- [sops](https://github.com/getsops/sops)
- [age](https://github.com/FiloSottile/age)

### Installation
TODO: Add the required structure to support installation via pipx
For now, you'll need to clone the repo, ideally set up a virtual environment and install the requirements. 

### Setup
Currently, sops-run assumes you're using `age` as your encryption key source, though I'd like to add support for external keys in the future. To get started, you'll need to create an ace key pair. The `age` and `age-keygen` man pages are pretty great, so please look to there for the most accurate instructions on how to do this. 

sops-run expects to find your key file in `~/.local/age`, and will choose the first file it finds in that directory. If you have multiple keys, or if you'd like to specify a specific key, you can use the `--key` argument or set the `SOPS_AGE_KEY_FILE` environment variable. Note that the environment variable will take precedence over the argument.


## Usage
Once your `age` key is all set up, the first thing you'll want to do is create a manifest, with the `--create` argument. (Example: `sops-run --create bash`). `sops-run` manifests are stored in `~/.config/sops-run`, and will create this directory if it doesn't exist when you create your first manifest. When you create a manifest, sops will open your default `$EDITOR`, and populate the file with an example yaml file. For more information on how this process works, see the `sops` documentation. Once you save your file and close your editor, sops will encrypt the file and save it in the manifest directory.

Once a manifest is created for a command, you can run it with `sops-run <command>`. (Example: `sops-run bash script.sh`) `sops-run` will look for a manifest with the same name as the first argument you provide. For example, if you run `sops-run bash script.py`, `sops-run` will load the manifest for `bash`. Currently, there is no way to override the manifest provided, but if you'd like to see this feature, please open an issue.

If you need to edit a manifest, you can use the `--edit` argument. (Example: `sops-run --edit bash`). This will open the manifest in your default `$EDITOR` and allow you to make changes. Once you save and close your editor, sops will re-encrypt the file and save it in the manifest directory.
