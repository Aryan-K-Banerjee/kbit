import argparse

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
    print("initialized .kbit folder")

def add():
    print("Added files to staging area")

def commit():
    print("Committed Changes")

def unknown():
    print("Unknown command")



if __name__ == "__main__":
    main()