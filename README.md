# KBIT
This is my version of git, made for learning purposes

I will start in Python implementing

- kbit init
- kbit add <filename>
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

## Step 2: kbit add