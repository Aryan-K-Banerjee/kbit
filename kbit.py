import argparse
import os
from hashlib import sha1

CWD = os.getcwd()
KBIT_D = os.path.join(CWD, ".kbit")
OBJECTS_D = os.path.join(KBIT_D, "objects")
REFS_D = os.path.join(KBIT_D, "refs", "heads")
HEAD = os.path.join(KBIT_D, "HEAD")
INDEX = os.path.join(KBIT_D, "index")

def main():
    parser = argparse.ArgumentParser(description="kbit command line parser")
    subparsers = parser.add_subparsers(dest="command")

    #init command
    p_init = subparsers.add_parser("init", help="Initialize a new kbit repo")

    #add command
    p_add = subparsers.add_parser("add", help="Add files to the staging area")
    p_add.add_argument("paths", nargs="+", help="Files or '.'")
    
    #commit command
    p_commit = subparsers.add_parser("commit", help="Commit staged changes")
    
    args = parser.parse_args()

    if args.command == "init":
        init()
    elif args.command == "add":
        add(args.paths)
    elif args.command == "commit":
        commit()
    else:
        unknown()

def init():
    # Checking if the .kbit folder is already initialized and if anything is missing
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

    #Initializing the actual .kbit folder structure
    os.makedirs(KBIT_D, exist_ok=True)
    os.makedirs(OBJECTS_D, exist_ok=True)
    os.makedirs(REFS_D, exist_ok=True)
    if not os.path.isfile(HEAD):            #ensuring the HEAD is initialized with a default branch
        open(HEAD, 'w').write("refs/heads/main")
    open(INDEX, 'a').close()

def add(paths):
    #Ensuring the Kbit Directory is initialized
    if not os.path.isdir(KBIT_D):
        print("No .kbit directory found! Run kbit init first")
        return
    
    #Getting all files that are added
    file_list = set()
    for path in paths:
        if not os.path.exists(path):
            print(path, "does not exist!")
        elif os.path.isfile(path):
            file_list.add(path)
        elif os.path.isdir(path):
            print(path, "is a dir")
            for root, dirs, files in os.walk(path):
                if ".kbit" in dirs:
                    dirs.remove(".kbit")
                    
                for f in files:
                    file_path = os.path.join(root, f)
                    file_list.add(file_path)
    
    # Getting the contents 
    for f in file_list:
        print(f)
        blob, b_hash = make_blob(f)
        obj_addr = ".kbit/objects/"+b_hash
        if os.path.isfile(obj_addr):
            print(f + " is not changed")
        else:
            obj = open(obj_addr, "wb")
            obj.write(blob)
            obj.close()

def hash_content(content):
    return sha1(content).hexdigest()

def make_blob(file_path):
    #make the blob header - blob <num_bytes>\0<content>
    content = open(file_path, "rb").read()
    num_bytes = len(content)
    header = "blob " + str(num_bytes) + "\0"
    blob = header.encode("utf-8") + content
    b_hash = hash_content(blob)

    return blob, b_hash

def commit():
    print("Committed Changes")

def unknown():
    print("Unknown command")



if __name__ == "__main__":
    main()