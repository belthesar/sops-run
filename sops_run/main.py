#!/usr/bin/env python3
"""
sops-run

Runs a command with secrets decrypted from sops files.
Cody Wilson <cody@codywilson.co>
"""
import argparse
import os
import shutil
from environs import Env
from subprocess import run

parser = argparse.ArgumentParser(description="Run a command with secrets decrypted from sops files.")
parser.add_argument("command", nargs="+", help="Command to run")
parser.add_argument("--create", action="store_true", help="Create a new sops-run manifest", default=False)
parser.add_argument("--edit", action="store_true", help="Edit a sops-run manifest", default=False)
parser.add_argument("--key", help="Path to age key to use for encryption/decryption", default=None)

def check_dependencies():
    if shutil.which("sops") is None:
        raise FileNotFoundError("sops not found in PATH! Ensure you've installed sops and try again. See the README for more information.")
    if shutil.which("age-keygen") is None:
        raise FileNotFoundError("age-keygen not found in PATH! Ensure you've installed age and try again. See the README for more information.")


def find_first_age_key():
    keys = []
    for key in os.listdir(os.path.expanduser("~/.local/age")):
        keys.append(os.path.join(os.path.expanduser("~/.local/age"), key))
        if len(keys) > 0:
            break
    if keys:
        key_path = os.path.realpath(keys[0])
        return key_path
    raise FileNotFoundError(f"No age keys found in ~/.local/age! Ensure you've created an age key and try again. See the README for more information.")
    

def get_recipient_key(key_file):
    get_recipient_key_command = ['age-keygen', '-y', key_file]
    get_recipient_key_command_output = list(run(get_recipient_key_command, capture_output=True, text=True).stdout.strip())
    get_recipient_key_command_output = [item for item in get_recipient_key_command_output if item]
    return get_recipient_key_command_output


env = Env()
env.read_env()
DEFAULT_AGE_KEY_RECIPIENT = get_recipient_key(find_first_age_key())
SOPS_AGE_KEY_FILE = env.str("SOPS_AGE_KEY", default=None)
SOPS_AGE_RECIPIENTS = env.list("SOPS_AGE_RECIPIENTS", subcast=str, default=list(DEFAULT_AGE_KEY_RECIPIENT))
SOPS_AGE_RECIPIENTS = [item for item in SOPS_AGE_RECIPIENTS if item] # removes empty strings from list


def main():
    args = parser.parse_args()
    if args.key:
        recipient_key = get_recipient_key(args.key)
        global SOPS_AGE_RECIPIENTS
        SOPS_AGE_RECIPIENTS = [recipient_key]
    if SOPS_AGE_KEY_FILE:
        recipient_key = get_recipient_key(SOPS_AGE_KEY_FILE)
        global SOPS_AGE_RECIPIENTS
        SOPS_AGE_RECIPIENTS = [recipient_key]
    if args.create:
        update_manifest(args.command)
    elif args.edit:
        update_manifest(args.command, edit=True)
    else:
        run_command(args.command)

def update_manifest(command, edit=False):
    if len(command) > 1:
        raise ValueError("Create argument only accepts one command")
    # Check if manifest already exists
    # First, test for .sops-run dir in home directory
    home_dir = os.path.expanduser("~")
    sops_run_dir = os.path.join(home_dir, ".sops-run")
    if not os.path.isdir(sops_run_dir):
        try:
            print("Creating .sops-run directory in home directory...")
            os.mkdir(sops_run_dir)
        except OSError:
            raise OSError("Could not create .sops-run directory in home directory")
            exit(1)
    # Next, test for manifest file
    manifest_file = os.path.join(sops_run_dir, command[0])
    if not edit and os.path.isfile(manifest_file):
        raise FileExistsError(f"A manifest file for {command[0]} already exists. Use --edit to edit it.")
        exit(1)
    if edit and not os.path.isfile(manifest_file):
        raise FileNotFoundError(f"No manifest file for {command[0]} exists. Use --create to create one.")
        exit(1)
    # Use sops to create a new manifest file
    sops_age_recipients_as_string = ','.join(SOPS_AGE_RECIPIENTS) if len(SOPS_AGE_RECIPIENTS) > 1 else SOPS_AGE_RECIPIENTS[0]
    sops_command = ["sops", "--age", sops_age_recipients_as_string, f'{manifest_file}.yml']
    if edit:
        print("Editing manifest file...")
    else:
        print("Creating manifest file...")
    create_file = run(sops_command)
    if create_file.returncode:
        print("Error creating/editing manifest file", f"stderr: {create_file.stderr}", f"stdout: {create_file.stdout}", sep=", ")
        exit(1)

def run_command(command):
    print()
    # Check if manifest exists
    # First, test for .sops-run dir in home directory
    home_dir = os.path.expanduser("~")
    sops_run_dir = os.path.join(home_dir, ".sops-run")
    if not os.path.isdir(sops_run_dir):
        raise FileNotFoundError("No .sops-run directory exists in home directory")
        exit(1)
    # Next, test for manifest file
    manifest_file = os.path.join(sops_run_dir, f'{command[0]}.yml')
    if not os.path.isfile(manifest_file):
        raise FileNotFoundError(f"No manifest file for {command[0]} exists. Use --create to create one.")
        exit(1)
    # Use sops exec-env to pass secrets as environment variables to command
    sops_command = ["sops", "exec-env", manifest_file, "'" + " ".join(command) + "'"]
    run(sops_command)

if __name__ == "__main__":
    main()