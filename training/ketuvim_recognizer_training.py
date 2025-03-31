import subprocess

def run_command(command):
    print(f"Executing: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"Error: Command failed - {command}")
        exit(result.returncode)

def main():
    commands = [
        "ketos compile --keep-empty-lines -f xml -o labelled.arrow *.xml",
        "ketos train -f binary -d mps --resize both -i pretrain_best.mlmodel -o ketuvim_recognizer -B 4 -r 0.0002 schedule cosine -u NFC --warmup 5000 --freeze-backbone 1000 labelled.arrow"
    ]
    
    for cmd in commands:
        run_command(cmd)

if __name__ == '__main__':
    main()