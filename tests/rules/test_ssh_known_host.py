import os
import pytest
from mock import Mock
from thefuck.main import Command
from thefuck.rules.ssh_known_hosts import match, get_new_command, remove_offending_keys


@pytest.fixture
def ssh_error(tmpdir):
    path = os.path.join(str(tmpdir), 'known_hosts')

    def reset(path):
        with open(path, 'w') as fh:
            lines = [
                '123.234.567.890 asdjkasjdakjsd\n'
                '98.765.432.321 ejioweojwejrosj\n'
                '111.222.333.444 qwepoiwqepoiss\n'
            ]
            fh.writelines(lines)

    def known_hosts(path):
        with open(path, 'r') as fh:
            return fh.readlines()

    reset(path)

    errormsg = u"""@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
The fingerprint for the RSA key sent by the remote host is
b6:cb:07:34:c0:a0:94:d3:0d:69:83:31:f4:c5:20:9b.
Please contact your system administrator.
Add correct host key in {0} to get rid of this message.
Offending RSA key in {0}:2
RSA host key for {1} has changed and you have requested strict checking.
Host key verification failed.""".format(path, '98.765.432.321')

    return errormsg, path, reset, known_hosts


def test_match(ssh_error):
    errormsg, _, _, _ = ssh_error
    assert match(Command('ssh', '', errormsg), None)
    assert match(Command('ssh', '', errormsg), None)
    assert match(Command('scp something something', '', errormsg), None)
    assert match(Command('scp something something', '', errormsg), None)
    assert not match(Command('', '', errormsg), None)
    assert not match(Command('notssh', '', errormsg), None)
    assert not match(Command('ssh', '', ''), None)


def test_remove_offending_keys(ssh_error):
    errormsg, path, reset, known_hosts = ssh_error
    command = Command('ssh user@host', '', errormsg)
    remove_offending_keys(command, None)
    expected = ['123.234.567.890 asdjkasjdakjsd\n', '111.222.333.444 qwepoiwqepoiss\n']
    assert known_hosts(path) == expected


def test_get_new_command(ssh_error, monkeypatch):
    errormsg, _, _, _ = ssh_error

    method = Mock()
    monkeypatch.setattr('thefuck.rules.ssh_known_hosts.remove_offending_keys', method)
    assert get_new_command(Command('ssh user@host', '', errormsg), None) == 'ssh user@host'
    assert method.call_count
