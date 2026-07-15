import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

#checking initialization
def test_kbit_init(tmp_path):
    from kbit import init

    #temp dir
    os.chdir(tmp_path)

    init()

    assert (tmp_path / ".kbit").is_dir()
    assert (tmp_path / ".kbit" / "objects").is_dir()
    assert (tmp_path / ".kbit" / "refs" / "heads").is_dir()
    assert (tmp_path / ".kbit" / "HEAD").is_file()
    assert (tmp_path / ".kbit" / "index").is_file()