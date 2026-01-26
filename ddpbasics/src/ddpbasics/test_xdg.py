from otvl_general.utils.xdg import xdg_config_dir


def test_xdg_wo_env_mkd(monkeypatch, tmp_path):
    home = str(tmp_path / "home")
    monkeypatch.setenv("HOME", home)
    cd = xdg_config_dir()
    assert cd == str(tmp_path / "home" / ".config")


def test_xdg_wo_env_no_mkd(monkeypatch, tmp_path):
    h2p = tmp_path / "home2"
    home2 = str(h2p)
    h2p.mkdir(0o770, parents=True)
    (h2p / ".config").mkdir(0o700)
    monkeypatch.setenv("HOME", home2)
    cd = xdg_config_dir()
    assert cd == str(tmp_path / "home2" / ".config")


def test_xdg_with_env(monkeypatch, tmp_path):
    xdg_cd = str(tmp_path / "xdg_cd")
    monkeypatch.setenv("XDG_CONFIG_DIR", xdg_cd)
    cd = xdg_config_dir()
    assert cd == str(xdg_cd)
