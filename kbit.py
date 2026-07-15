import argparse
import os

def main():
    parser = argparse.ArgumentParser(description="kbit command line parser")
    subparsers = parser.add_subparsers(dest="command")

    p_init = subparsers.add_parser("init", help="Initialize a new kbit repo")
    p_add = subparsers.add_parser("add", help="Add files to the staging area")
    p_commit = subparsers.add_parser("commit", help="Commit staged changes")
    args = parser.parse_args()

    if args.command == "init":
        init()
    elif args.command == "add":
        add()
    elif args.command == "commit":
        commit()
    else:
        unknown()

def init():
    CWD = os.getcwd()
    KBIT_D = os.path.join(CWD, ".kbit")
    OBJECTS_D = os.path.join(KBIT_D, "objects")
    REFS_D = os.path.join(KBIT_D, "refs", "heads")
    HEAD = os.path.join(KBIT_D, "HEAD")
    INDEX = os.path.join(KBIT_D, "index")

    if os.path.isdir(KBIT_D):
        print(".kbit directory already exists!")
        if not os.path.isdir(OBJECTS_D):
           print("objects/ directory missing, will be initialized")
        if not os.path.isdir(REFS_D):
            print("refs/heads/ directory missing, will be initialized")
        if not os.path.isfile(HEAD):
            print("HEAD missing, will be initialized")
        if not os.path.isfile(INDEX):
            print("index is missing, will be initialized")
    else:
        print(".kbit directory initialized!")

    os.makedirs(KBIT_D, exist_ok=True)
    os.makedirs(OBJECTS_D, exist_ok=True)
    os.makedirs(REFS_D, exist_ok=True)
    open(HEAD, 'a').close()
    open(INDEX, 'a').close()

def add():
    print("Added files to staging area")

def commit():
    print("Committed Changes")

def unknown():
    print("Unknown command")



if __name__ == "__main__":
    main()