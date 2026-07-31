import importlib
import os
import shutil
import sys
from hashlib import sha1
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def fresh_kbit(tmp_path, monkeypatch):
    """
    Load a fresh copy of kbit from inside a temporary repository.

    This is necessary because kbit.py calculates CWD and all .kbit paths
    when the module is imported.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(PROJECT_ROOT))

    sys.modules.pop("kbit", None)
    kbit = importlib.import_module("kbit")

    yield kbit, tmp_path

    sys.modules.pop("kbit", None)


def read_index(kbit):
    """Return the KBIT index as a path -> blob hash dictionary."""
    index_map = {}

    with open(kbit.INDEX, "r") as index_file:
        for line in index_file:
            line = line.strip()

            if not line:
                continue

            path, blob_hash = line.split("\t", 1)
            index_map[path] = blob_hash

    return index_map


def read_object(kbit, object_hash):
    """Read and separate a stored KBIT object's header and payload."""
    object_path = Path(kbit.OBJECTS_D) / object_hash
    object_data = object_path.read_bytes()

    header, payload = object_data.split(b"\0", 1)

    object_type, size = header.decode("utf-8").split(" ", 1)

    assert int(size) == len(payload)

    return object_type, payload


def get_current_commit_hash(kbit):
    """Read the commit hash referenced by the current branch."""
    branch = Path(kbit.HEAD).read_text().strip()
    branch_path = Path(kbit.KBIT_D) / branch

    return branch_path.read_text().strip()


def get_tree_hash_from_commit(kbit, commit_hash):
    """Read the tree hash from a commit object."""
    object_type, commit_content = read_object(kbit, commit_hash)

    assert object_type == "commit"

    tree_line = commit_content.split(b"\n", 1)[0]
    label, tree_hash = tree_line.split(b"\t", 1)

    assert label == b"tree"

    return tree_hash.decode("utf-8")


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

def test_kbit_init(fresh_kbit):
    kbit, tmp_path = fresh_kbit

    kbit.init()

    assert (tmp_path / ".kbit").is_dir()
    assert (tmp_path / ".kbit" / "objects").is_dir()
    assert (tmp_path / ".kbit" / "refs" / "heads").is_dir()
    assert (tmp_path / ".kbit" / "HEAD").is_file()
    assert (tmp_path / ".kbit" / "index").is_file()

    assert (
        tmp_path / ".kbit" / "HEAD"
    ).read_text() == "refs/heads/main"

    assert (
        tmp_path / ".kbit" / "index"
    ).read_text() == ""


def test_init_can_be_run_more_than_once(fresh_kbit):
    kbit, tmp_path = fresh_kbit

    kbit.init()
    kbit.init()

    assert (tmp_path / ".kbit").is_dir()
    assert (tmp_path / ".kbit" / "objects").is_dir()
    assert (tmp_path / ".kbit" / "refs" / "heads").is_dir()
    assert (tmp_path / ".kbit" / "HEAD").is_file()
    assert (tmp_path / ".kbit" / "index").is_file()

    assert (
        tmp_path / ".kbit" / "HEAD"
    ).read_text() == "refs/heads/main"


def test_init_recreates_missing_structure(fresh_kbit):
    kbit, tmp_path = fresh_kbit

    kbit.init()

    shutil.rmtree(tmp_path / ".kbit" / "objects")
    os.remove(tmp_path / ".kbit" / "index")

    kbit.init()

    assert (tmp_path / ".kbit" / "objects").is_dir()
    assert (tmp_path / ".kbit" / "index").is_file()


# ---------------------------------------------------------------------------
# add and blobs
# ---------------------------------------------------------------------------

def test_add_file_creates_blob_and_index_entry(fresh_kbit):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    file_content = b"Hello from KBIT!"
    (tmp_path / "hello.txt").write_bytes(file_content)

    kbit.add(["hello.txt"])

    blob = (
        f"blob {len(file_content)}\0".encode("utf-8")
        + file_content
    )
    expected_hash = sha1(blob).hexdigest()

    index_map = read_index(kbit)

    assert index_map == {
        "hello.txt": expected_hash
    }

    object_path = (
        tmp_path
        / ".kbit"
        / "objects"
        / expected_hash
    )

    assert object_path.is_file()
    assert object_path.read_bytes() == blob


def test_adding_unchanged_file_reuses_blob(fresh_kbit):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    (tmp_path / "hello.txt").write_text("unchanged")

    kbit.add(["hello.txt"])

    first_index = read_index(kbit)
    first_objects = set(
        os.listdir(tmp_path / ".kbit" / "objects")
    )

    kbit.add(["hello.txt"])

    second_index = read_index(kbit)
    second_objects = set(
        os.listdir(tmp_path / ".kbit" / "objects")
    )

    assert first_index == second_index
    assert first_objects == second_objects
    assert len(second_objects) == 1


def test_modifying_file_updates_index_hash(fresh_kbit):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    file_path = tmp_path / "hello.txt"
    file_path.write_text("version one")

    kbit.add(["hello.txt"])

    first_hash = read_index(kbit)["hello.txt"]

    file_path.write_text("version two")

    kbit.add(["hello.txt"])

    second_hash = read_index(kbit)["hello.txt"]

    assert first_hash != second_hash

    assert (
        tmp_path / ".kbit" / "objects" / first_hash
    ).is_file()

    assert (
        tmp_path / ".kbit" / "objects" / second_hash
    ).is_file()


def test_add_multiple_files(fresh_kbit):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    (tmp_path / "one.txt").write_text("one")
    (tmp_path / "two.txt").write_text("two")

    kbit.add(["one.txt", "two.txt"])

    index_map = read_index(kbit)

    assert set(index_map) == {
        "one.txt",
        "two.txt",
    }


def test_add_directory_recursively(fresh_kbit):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "nested").mkdir()

    (tmp_path / "src" / "main.py").write_text(
        "print('main')"
    )
    (tmp_path / "src" / "nested" / "utils.py").write_text(
        "VALUE = 1"
    )

    kbit.add(["src"])

    index_map = read_index(kbit)

    assert set(index_map) == {
        os.path.join("src", "main.py"),
        os.path.join("src", "nested", "utils.py"),
    }


def test_add_dot_does_not_track_kbit_directory(fresh_kbit):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    (tmp_path / "hello.txt").write_text("hello")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text(
        "print('hello')"
    )

    kbit.add(["."])

    index_map = read_index(kbit)

    normalized_paths = {
        os.path.normpath(path)
        for path in index_map
    }

    assert normalized_paths == {
        "hello.txt",
        os.path.join("src", "main.py"),
    }

    assert all(
        ".kbit" not in path
        for path in normalized_paths
    )


def test_add_missing_file_does_not_change_index(
    fresh_kbit,
    capsys,
):
    kbit, _ = fresh_kbit
    kbit.init()

    kbit.add(["missing.txt"])

    output = capsys.readouterr().out

    assert "missing.txt does not exist!" in output
    assert read_index(kbit) == {}


# ---------------------------------------------------------------------------
# rm
# ---------------------------------------------------------------------------

def test_rm_removes_file_from_index_only(fresh_kbit):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    file_path = tmp_path / "hello.txt"
    file_path.write_text("keep this working file")

    kbit.add(["hello.txt"])

    blob_hash = read_index(kbit)["hello.txt"]
    blob_path = (
        tmp_path / ".kbit" / "objects" / blob_hash
    )

    kbit.rm("hello.txt")

    assert read_index(kbit) == {}

    # rm should not delete the working file.
    assert file_path.is_file()
    assert file_path.read_text() == "keep this working file"

    # rm should not delete the stored object.
    assert blob_path.is_file()


def test_rm_unknown_file_leaves_index_unchanged(
    fresh_kbit,
    capsys,
):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    (tmp_path / "tracked.txt").write_text("tracked")
    kbit.add(["tracked.txt"])

    index_before = read_index(kbit)

    kbit.rm("missing.txt")

    output = capsys.readouterr().out

    assert "File not in index" in output
    assert read_index(kbit) == index_before


# ---------------------------------------------------------------------------
# commit, tree, and refs
# ---------------------------------------------------------------------------

def test_first_commit_creates_tree_and_commit_objects(
    fresh_kbit,
):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    (tmp_path / "hello.txt").write_text("hello")

    kbit.add(["hello.txt"])
    kbit.commit("Initial commit")

    branch_path = (
        tmp_path
        / ".kbit"
        / "refs"
        / "heads"
        / "main"
    )

    assert branch_path.is_file()

    commit_hash = branch_path.read_text().strip()

    assert commit_hash

    commit_type, commit_content = read_object(
        kbit,
        commit_hash,
    )

    assert commit_type == "commit"
    assert b"parent\t" not in commit_content
    assert commit_content.endswith(b"Initial commit")

    tree_hash = get_tree_hash_from_commit(
        kbit,
        commit_hash,
    )

    tree_type, tree_content = read_object(
        kbit,
        tree_hash,
    )

    assert tree_type == "tree"

    blob_hash = read_index(kbit)["hello.txt"]

    expected_tree_entry = (
        f"hello.txt\t{blob_hash}\n".encode("utf-8")
    )

    assert tree_content == expected_tree_entry


def test_second_commit_points_to_first_commit(
    fresh_kbit,
):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    file_path = tmp_path / "hello.txt"
    file_path.write_text("version one")

    kbit.add(["hello.txt"])
    kbit.commit("First commit")

    first_commit_hash = get_current_commit_hash(kbit)

    file_path.write_text("version two")

    kbit.add(["hello.txt"])
    kbit.commit("Second commit")

    second_commit_hash = get_current_commit_hash(kbit)

    assert second_commit_hash != first_commit_hash

    object_type, commit_content = read_object(
        kbit,
        second_commit_hash,
    )

    assert object_type == "commit"

    expected_parent = (
        f"parent\t{first_commit_hash}\n".encode("utf-8")
    )

    assert expected_parent in commit_content
    assert commit_content.endswith(b"Second commit")

    # The first commit object must remain available.
    assert (
        tmp_path
        / ".kbit"
        / "objects"
        / first_commit_hash
    ).is_file()


def test_branch_ref_points_to_latest_commit(
    fresh_kbit,
):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    file_path = tmp_path / "hello.txt"
    file_path.write_text("one")

    kbit.add(["hello.txt"])
    kbit.commit("Commit one")

    first_hash = get_current_commit_hash(kbit)

    file_path.write_text("two")

    kbit.add(["hello.txt"])
    kbit.commit("Commit two")

    second_hash = get_current_commit_hash(kbit)

    branch_path = (
        tmp_path
        / ".kbit"
        / "refs"
        / "heads"
        / "main"
    )

    assert branch_path.read_text() == second_hash
    assert first_hash != second_hash


def test_tree_entries_are_sorted(fresh_kbit):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    (tmp_path / "zebra.txt").write_text("z")
    (tmp_path / "apple.txt").write_text("a")
    (tmp_path / "middle.txt").write_text("m")

    kbit.add([
        "zebra.txt",
        "apple.txt",
        "middle.txt",
    ])

    kbit.commit("Sorted tree")

    commit_hash = get_current_commit_hash(kbit)
    tree_hash = get_tree_hash_from_commit(
        kbit,
        commit_hash,
    )

    object_type, tree_content = read_object(
        kbit,
        tree_hash,
    )

    assert object_type == "tree"

    paths = []

    for line in tree_content.splitlines():
        path, _ = line.split(b"\t", 1)
        paths.append(path.decode("utf-8"))

    assert paths == sorted(paths)


# ---------------------------------------------------------------------------
# checkout
# ---------------------------------------------------------------------------

def test_checkout_restores_text_file(fresh_kbit):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    file_path = tmp_path / "hello.txt"
    file_path.write_text("committed contents")

    kbit.add(["hello.txt"])
    kbit.commit("Save hello")

    commit_hash = get_current_commit_hash(kbit)

    file_path.write_text("changed contents")

    kbit.checkout(commit_hash)

    assert file_path.read_text() == "committed contents"


def test_checkout_restores_binary_file(fresh_kbit):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    original_content = bytes([
        0,
        1,
        2,
        3,
        255,
        128,
        64,
    ])

    binary_path = tmp_path / "data.bin"
    binary_path.write_bytes(original_content)

    kbit.add(["data.bin"])
    kbit.commit("Save binary")

    commit_hash = get_current_commit_hash(kbit)

    binary_path.write_bytes(b"different")

    kbit.checkout(commit_hash)

    assert binary_path.read_bytes() == original_content


def test_checkout_recreates_parent_directories(
    fresh_kbit,
):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    nested_dir = tmp_path / "src" / "nested"
    nested_dir.mkdir(parents=True)

    nested_file = nested_dir / "main.py"
    nested_file.write_text("print('restored')")

    kbit.add(["src"])
    kbit.commit("Save nested file")

    commit_hash = get_current_commit_hash(kbit)

    shutil.rmtree(tmp_path / "src")

    assert not nested_file.exists()

    kbit.checkout(commit_hash)

    assert nested_file.is_file()
    assert nested_file.read_text() == "print('restored')"


def test_checkout_restores_multiple_files(fresh_kbit):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    (tmp_path / "one.txt").write_text("one")
    (tmp_path / "two.txt").write_text("two")

    kbit.add(["one.txt", "two.txt"])
    kbit.commit("Save both files")

    commit_hash = get_current_commit_hash(kbit)

    os.remove(tmp_path / "one.txt")
    os.remove(tmp_path / "two.txt")

    kbit.checkout(commit_hash)

    assert (tmp_path / "one.txt").read_text() == "one"
    assert (tmp_path / "two.txt").read_text() == "two"


def test_checkout_rejects_unknown_hash(
    fresh_kbit,
    capsys,
):
    kbit, _ = fresh_kbit
    kbit.init()

    kbit.checkout("does-not-exist")

    output = capsys.readouterr().out

    assert "Commit not found!" in output


def test_checkout_rejects_blob_hash(
    fresh_kbit,
    capsys,
):
    kbit, tmp_path = fresh_kbit
    kbit.init()

    (tmp_path / "hello.txt").write_text("hello")
    kbit.add(["hello.txt"])

    blob_hash = read_index(kbit)["hello.txt"]

    kbit.checkout(blob_hash)

    output = capsys.readouterr().out

    assert "Hash is not a commit!" in output