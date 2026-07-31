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
    p_commit.add_argument("-m", required=True, help="Commit message")

    #rm command
    p_rm = subparsers.add_parser("rm", help="Remove any tracked file from index")
    p_rm.add_argument("file", help="File to remove")

    #checkout command
    p_checkout = subparsers.add_parser("checkout", help="Checkout a specific commit")
    p_checkout.add_argument("hash", help="Commit hash to checkout")

    args = parser.parse_args()

    if args.command == "init":
        init()
    elif args.command == "add":
        add(args.paths)
    elif args.command == "commit":
        commit(args.m)
    elif args.command == "rm":
        rm(args.file)
    elif args.command == "checkout":
        checkout(args.hash)
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

    #getting currently indexed files
    index_map = {}
    with open(INDEX, 'r') as index_file:
        for line in index_file:
            elements = line.strip().split('\t')
            index_map[elements[0]] = elements[1]

    #Getting all files that are added
    file_list = set()
    for path in paths:
        if not os.path.exists(path):
            print(path, "does not exist!")
        elif os.path.isfile(path):
            file_list.add(path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                if ".kbit" in dirs:
                    dirs.remove(".kbit")
                    
                for f in files:
                    file_path = os.path.join(root, f)
                    file_list.add(file_path)

    # Blobbing and updating index
    for f in file_list:
        print(f)
        blob, b_hash = make_blob(f)
        obj_addr = OBJECTS_D + '/' + b_hash
        if not os.path.isfile(obj_addr):
            obj = open(obj_addr, "wb")
            obj.write(blob)
            obj.close()

        if f not in index_map or index_map[f] != b_hash:
            print(f + " was updated!")
        index_map[f] = b_hash

    # Writing back to the index file
    with open(INDEX, 'w') as index_file:
        for key, value in index_map.items():
            index_file.write(key + "\t" + value + "\n")
        
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

def commit(message):
    #Ensuring the Kbit Directory is initialized
    if not os.path.isdir(KBIT_D):
        print("No .kbit directory found! Run kbit init first")
        return

    tree_obj, t_hash = make_tree()
    branch = open(HEAD, "r").read()
    previous_commit_hash = None if not os.path.isfile(KBIT_D + "/" + branch) else open(KBIT_D + "/" + branch, "r").read().strip()
    commit_obj, c_hash = make_commit(t_hash, previous_commit_hash, message)
    tree_addr = OBJECTS_D + '/' + t_hash
    commit_addr = OBJECTS_D + "/" + c_hash
    open(tree_addr, "wb").write(tree_obj)
    open(commit_addr, "wb").write(commit_obj)
    open(KBIT_D + "/" + branch, 'w').write(c_hash)
    print("Committed changes: " + c_hash)

def make_tree():
    index_map = {}
    with open(INDEX, 'r') as index_file:
        for line in index_file:
            elements = line.strip().split('\t')
            index_map[elements[0]] = elements[1]
    sorted_items = sorted(index_map.items())
    content = b""
    for key, val in sorted_items:
        content += f"{key}\t{val}\n".encode("utf-8")
    num_bytes = len(content)
    header = "tree " + str(num_bytes) + "\0"
    tree = header.encode("utf-8") + content
    t_hash = hash_content(tree)
    return tree, t_hash

def make_commit(t_hash, previous_commit_hash, message):
    content = f"tree\t{t_hash}\n"
    if previous_commit_hash is not None:
        content += f"parent\t{previous_commit_hash}\n"
    content += message
    content = content.encode("utf-8")
    num_bytes = len(content)
    header = "commit " + str(num_bytes) + "\0"
    commit = header.encode("utf-8") + content
    c_hash = hash_content(commit)
    return commit, c_hash

def rm(file_trm):
    #Ensuring the Kbit Directory is initialized
    if not os.path.isdir(KBIT_D):
        print("No .kbit directory found! Run kbit init first")
        return

    #Opening the index as a hashmap
    index_map = {}
    with open(INDEX, 'r') as index_file:
        for line in index_file:
            elements = line.strip().split('\t')
            index_map[elements[0]] = elements[1]

    #Looking for and removing target with message
    if file_trm in index_map:
        del index_map[file_trm]
        print(file_trm + " is removed!")
    else:
        print("File not in index")

    with open(INDEX, 'w') as index_file:
            for key, value in index_map.items():
                index_file.write(key + "\t" + value + "\n")

def checkout(commit_hash):
    #Finding commit hash and object
    commit_addr = OBJECTS_D + "/" + commit_hash

    if not os.path.isfile(commit_addr):
        print("Commit not found!")
        return

    commit_obj = open(commit_addr, "rb").read()
    c_header, c_content = commit_obj.split(b"\0", 1)

    if not c_header.startswith(b"commit "):
        print("Hash is not a commit!")
        return

    #Isolating tree line and finding tree object
    t_line = c_content.split(b"\n", 1)[0]
    t_name, t_hash = t_line.split(b"\t", 1)

    if t_name != b"tree":
        print("Commit does not contain a valid tree!")
        return

    t_hash = t_hash.decode("utf-8")
    tree_addr = OBJECTS_D + "/" + t_hash

    if not os.path.isfile(tree_addr):
        print("Tree not found!")
        return

    #Finding tree content
    tree_obj = open(tree_addr, "rb").read()
    t_header, t_content = tree_obj.split(b"\0", 1)

    if not t_header.startswith(b"tree "):
        print("Hash for tree is not a tree!")
        return

    #Finding the individual files
    lines = t_content.split(b"\n")
    for line in lines:
        #skipping any empty lines
        if not line:
            continue

        #extracting files
        file_name, blob_hash = line.split(b'\t', 1)
        file_name = file_name.decode("utf-8")
        blob_hash = blob_hash.decode("utf-8")

        #reconstructing blob
        blob_addr = OBJECTS_D + '/' + blob_hash
        if not os.path.isfile(blob_addr):
            print("Blob not found for", file_name)
            return
        blob_obj = open(blob_addr, 'rb').read()
        b_header, b_content = blob_obj.split(b'\0', 1)

        if not b_header.startswith(b'blob '):
            print("Hash for", file_name, "is not a blob!")
            return

        #making sure to recreate any parent directories
        parent_dir = os.path.dirname(file_name)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        open(file_name, 'wb').write(b_content)
        print(file_name, "was restored!")

def unknown():
    print("Unknown command")



if __name__ == "__main__":
    main()