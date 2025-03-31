import subprocess

def run_command(command):
    print(f"Executing: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"Error: Command failed - {command}")
        exit(result.returncode)

def main():
    commands = [
        "ketos compile --keep-empty-lines -f xml -o foo.arrow *.xml",
        "ketos pretrain --device mps --batch-size 4 -o pretrain_model --mask-width 4 --mask-probability 0.2 --num-negatives 3 -f binary foo.arrow"
    ]
    
    for cmd in commands:
        run_command(cmd)

if __name__ == '__main__':
    main()