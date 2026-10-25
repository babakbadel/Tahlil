import os
from pathlib import Path
import subprocess
import sys

HELPER = Path(__file__).resolve().parents[1] / 'scripts/commit_outputs.py'


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True).stdout.strip()


def test_output_push_preserves_concurrent_code_changes(tmp_path):
    remote, producer, other = (tmp_path / name for name in ('remote.git', 'producer', 'other'))
    subprocess.run(['git', 'init', '--bare', '--initial-branch=main', str(remote)], check=True, capture_output=True)
    subprocess.run(['git', 'clone', str(remote), str(producer)], check=True, capture_output=True)
    git(producer, 'config', 'user.name', 'Test')
    git(producer, 'config', 'user.email', 'test@example.com')
    (producer / 'reports').mkdir()
    (producer / 'reports/result.json').write_text('old')
    (producer / 'code.py').write_text('old code')
    git(producer, 'add', '.')
    git(producer, 'commit', '-m', 'initial')
    git(producer, 'push', 'origin', 'main')
    subprocess.run(['git', 'clone', str(remote), str(other)], check=True, capture_output=True)
    git(other, 'config', 'user.name', 'Test')
    git(other, 'config', 'user.email', 'test@example.com')
    (other / 'code.py').write_text('new code')
    (other / 'reports/result.json').write_text('concurrent snapshot')
    git(other, 'add', '.')
    git(other, 'commit', '-m', 'concurrent code and output')
    git(other, 'push', 'origin', 'main')
    (producer / 'reports/result.json').write_text('latest snapshot')
    git(producer, 'add', 'reports/result.json')
    subprocess.run([sys.executable, str(HELPER)], cwd=producer, env={**os.environ, 'GITHUB_REF': 'refs/heads/main'}, check=True, capture_output=True)
    assert (producer / 'code.py').read_text() == 'new code'
    assert (producer / 'reports/result.json').read_text() == 'latest snapshot'
    assert git(producer, 'rev-parse', 'HEAD') == git(remote, 'rev-parse', 'main')


def test_feature_branch_cannot_publish_to_main(tmp_path):
    result = subprocess.run([sys.executable, str(HELPER)], cwd=tmp_path, env={**os.environ, 'GITHUB_REF': 'refs/heads/fix'}, capture_output=True, text=True)
    assert result.returncode == 0
    assert 'skipped' in result.stdout
