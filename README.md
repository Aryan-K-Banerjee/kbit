# KBIT
This is my version of git, made for learning purposes

I will start in Python implementing

- kbit init
- kbit add <files>
- kbit commit -m "<message>"

## Env and Structure:
I am using uv to create the venv and manage the python version. The version I am using is 3.12.13 as it is stable and the goal is setup speed. Pytest is used for testing

File Structure:
I am keeping it simple, just a python file, a shell script to use the tool directly, some tests and fake repo

kbit/
    README.md
    kbit.py                         //The main python file
    kbit                            //The shell script to run the tool directly
    tests/                          //Tests to automate checking the tool
    playground/                     //The fake repo so where tests will run

## Step 1
Starting with: kbit init

I will create a .kbit folder within which I will have the standard 4 things. 

.kbit/
    objects/
    refs/
        heads/
    HEAD
    index

- objects/          holds the hashed object data like file contents, snapshots, commits
- refs/heads/       holds the local branch pointers
- HEAD              holds the current branch being checked out
- index             is the staging area

So the git init command will be a function init() in the python file which will basically create the .kbit folder in the repo root and ensure what to do if a kbit folder already exists. I will also write tests to ensure this works

Also the HEAD when initially created points to a default branch, like main and it points to say refs/heads/main as that is where the commit hash will be.

## Step 0.5 (Before Step 1)
I realized I need to make the parser first so I will do that. I will start within python only for now, have it take in the commands and keep things simple for now.

## Step 0.75 (Testing)
I also added testing through pytest and will write unit tests as a practice

## Step 2: kbit add <files>
This command will add all changes that you want to track

First read all files sent in the command using os.walk
Then make sure each file is added uniquely using a set
Then get each file's content and combine it with a header to make a blob
Hash the Blob to check whether the blob is unique/the file content already is saved
Then check whether the file is tracked in the index, if it isn't add it with the blob hash, if it already is tracked, check the hash and make sure it is updated. Technically, it doesn't matter/ you don't need to check the hash, as you can overwrite it without consequences.
This basically makes sure the index keeps track of the current changes that are added.

I am seperately going to add a delete command to remove a file from the index as implementing that within add is a lot of code and kind of besides the point of understanding how git works.

## Step 3: kbit commit -m "<message>"
This basically allows you to commit the changes you make. 

First make a tree of the current index which is basically the latest filepaths and blob hashes that were added
Combine the tree content with a tree header and hash it and store it
Make a commit object which points to the tree, previous commit, and has the message
If there is no previous commit, it only has the tree and message
Hash and store this commit and then update the current branch reference by going to HEAD to get the current branch, and then writing the latest commit to that location.

Now that this is done I will also add a checkout command

## Step 4: kbit rm <filename> and kbit checkout <commit_hash>  
These are the final two commands in this project which are mostly added for posterity and so the project is functional enough to use if needed. I will also add some tests to ensure the project works as intended