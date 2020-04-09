# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
""" Test pmb/config/pmaports.py """
import pytest
import sys

import pmb_test
import pmb_test.const
import pmb_test.git
import pmb.config
import pmb.config.workdir
import pmb.config.pmaports


@pytest.fixture
def args(request):
    import pmb.parse
    cfg = f"{pmb_test.const.testdata}/channels.cfg"
    sys.argv = ["pmbootstrap.py", "--config-channels", cfg, "init"]
    args = pmb.parse.arguments()
    args.log = args.work + "/log_testsuite.txt"
    pmb.helpers.logging.init(args)
    request.addfinalizer(args.logfd.close)
    return args


def test_switch_to_channel_branch(args, monkeypatch, tmpdir):
    path, run_git = pmb_test.git.prepare_tmpdir(args, monkeypatch, tmpdir)
    args.aports = path

    # Pretend to have channel=edge in pmaports.cfg
    def read_config(args):
        return {"channel": "edge"}
    monkeypatch.setattr(pmb.config.pmaports, "read_config", read_config)

    # Success: Channel does not change
    func = pmb.config.pmaports.switch_to_channel_branch
    assert func(args, "edge") is False

    # Fail: git error (could be any error, but here: branch does not exist)
    with pytest.raises(RuntimeError) as e:
        func(args, "stable")
    assert str(e.value).startswith("Failed to switch branch")

    # Success: switch channel and change branch
    run_git(["checkout", "-b", "v20.05"])
    run_git(["checkout", "master"])
    assert func(args, "stable") is True
    branch = pmb.helpers.git.rev_parse(args, path, extra_args=["--abbrev-ref"])
    assert branch == "v20.05"
