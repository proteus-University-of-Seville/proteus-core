"""Git operations, independent of the UI and safe to run on a worker thread.

Paths are repository-relative; commands never use a shell. Authentication is
handled by Git's credential helper / SSH agent, never stored by PROTEUS.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess


class GitError(RuntimeError):
    """An actionable Git failure, including stderr from hooks and transports."""


@dataclass(frozen=True)
class GitFile:
    path: str
    index: str
    worktree: str
    original: str | None = None

    @property
    def conflicted(self) -> bool:
        return self.index + self.worktree in {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}


@dataclass(frozen=True)
class GitStatus:
    root: Path
    branch: str
    upstream: str
    ahead: int
    behind: int
    files: tuple[GitFile, ...]
    operation: str = ""
    remotes: tuple[tuple[str, str], ...] = ()
    has_stash: bool = False
    has_commits: bool = True


@dataclass(frozen=True)
class GitCommit:
    oid: str
    parents: tuple[str, ...]
    author: str
    date: str
    references: str
    subject: str


@dataclass(frozen=True)
class GitReference:
    name: str
    full_name: str
    kind: str
    oid: str
    author: str
    date: str
    subject: str
    upstream: str = ""
    tracking: str = ""


@dataclass(frozen=True)
class GitWorktree:
    path: str
    branch: str
    oid: str
    bare: bool = False
    locked: str | None = None
    prunable: str | None = None


class GitService:
    """One service per job. The caller serializes jobs for a repository."""

    def __init__(self, directory: Path | str, executable: str = "git", trusted_root: Path | None = None):
        self.directory = Path(directory).resolve()
        self.trusted_root = trusted_root
        self.executable = shutil.which(executable)
        if not self.executable:
            raise GitError("Git is not installed or its executable is not on PATH.")

    def run(self, *args: str, check: bool = True, timeout: int = 120, input_data: bytes | None = None, binary: bool = False) -> str | bytes:
        env = os.environ.copy()
        # Do not let the editor's own Git environment redirect this repository.
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
            env.pop(key, None)
        env.update(GIT_TERMINAL_PROMPT="0", GIT_EDITOR="true", GIT_SEQUENCE_EDITOR="true", LC_ALL="C", LANG="C")
        try:
            result = subprocess.run(
                [self.executable, *(["-c", "safe.directory=" + self.trusted_root.resolve().as_posix()] if self.trusted_root else []),
                 "--no-pager",
                 # stash uses internal pathspecs (notably :/) when cleaning saved files.
                 *(["--literal-pathspecs"] if not args or args[0] != "stash" else []), *args],
                cwd=self.directory, env=env, capture_output=True, input=input_data,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as error:
            raise GitError("Git timed out. Check the repository state before retrying.") from error
        except OSError as error:
            raise GitError(str(error)) from error
        output = result.stdout.decode("utf-8", errors="replace")
        if check and result.returncode:
            raise GitError(result.stderr.decode("utf-8", errors="replace").strip() or output.strip() or "Git failed.")
        return result.stdout if binary else output

    def root(self) -> Path | None:
        # An exit code is checked separately so ownership / permission failures
        # are not mistaken for a missing repository and offered an init button.
        try:
            return Path(self.run("rev-parse", "--show-toplevel").strip())
        except GitError as error:
            if "not a git repository" in str(error).lower():
                return None
            raise

    @staticmethod
    def parse_files(output: str) -> tuple[GitFile, ...]:
        records = iter(output.split("\0"))
        files = []
        for record in records:
            if not record:
                continue
            index, worktree, path = record[0], record[1], record[3:]
            original = next(records) if index in "RC" or worktree in "RC" else None
            files.append(GitFile(path, index, worktree, original))
        return tuple(files)

    def status(self) -> GitStatus | None:
        root = self.root()
        if root is None:
            return None
        self.directory = root
        branch = self.run("symbolic-ref", "--quiet", "--short", "HEAD", check=False).strip()
        if not branch:
            branch = "HEAD " + self.run("rev-parse", "--short", "HEAD").strip()
        upstream = self.run("rev-parse", "--abbrev-ref", "@{upstream}", check=False).strip()
        # rev-parse may echo the unresolved argument on an unborn branch.
        if upstream == "@{upstream}":
            upstream = ""
        ahead = behind = 0
        if upstream:
            counts = self.run("rev-list", "--left-right", "--count", "HEAD...@{upstream}").split()
            ahead, behind = map(int, counts)
        operation = ""
        git_directory = Path(self.run("rev-parse", "--absolute-git-dir").strip())
        for marker, name in (("MERGE_HEAD", "merge"), ("rebase-merge", "rebase"),
                             ("rebase-apply", "rebase"), ("CHERRY_PICK_HEAD", "cherry-pick"),
                             ("REVERT_HEAD", "revert")):
            if (git_directory / marker).exists():
                operation = name
                break
        remotes = []
        for line in self.run("remote", "-v").splitlines():
            fields = line.split()
            if len(fields) >= 3 and fields[-1] == "(fetch)":
                remotes.append((fields[0], fields[1]))
        return GitStatus(root, branch, upstream, ahead, behind,
                         self.parse_files(self.run("status", "--porcelain=v1", "-z", "--untracked-files=all")), operation, tuple(remotes),
                         bool(self.run("rev-parse", "--verify", "--quiet", "refs/stash", check=False).strip()),
                         bool(self.run("rev-parse", "--verify", "--quiet", "HEAD", check=False).strip()))

    def stage(self, paths: list[str]) -> str:
        if not paths:
            raise GitError("Select at least one file.")
        return self.run("add", "--", *paths)

    def unstage(self, paths: list[str]) -> str:
        if not paths:
            raise GitError("Select at least one file.")
        if self.run("rev-parse", "--verify", "HEAD", check=False).strip():
            return self.run("reset", "HEAD", "--", *paths)
        return self.run("rm", "--cached", "--force", "--", *paths)

    def commit(self, message: str) -> str:
        if not message.strip():
            raise GitError("Enter a commit message.")
        return self.run("commit", "-m", message)

    def branches(self) -> list[str]:
        return [b for b in self.run("for-each-ref", "--format=%(refname:short)",
                                   "refs/heads", "refs/remotes").splitlines() if not b.endswith("/HEAD")]

    def switch(self, branch: str, create: bool = False, remote_reference: bool = False) -> str:
        self.run("check-ref-format", "--branch", branch)
        if create:
            return self.run("switch", "-c", branch)
        local = "" if remote_reference else self.run("show-ref", "--verify", "refs/heads/" + branch, check=False).strip()
        remote = self.run("show-ref", "--verify", "refs/remotes/" + branch, check=False).strip()
        if remote and not local:
            remote_ref = 'refs/remotes/' + branch
            for line in self.run('for-each-ref', '--format=%(refname)%00%(upstream)', 'refs/heads').splitlines():
                name, upstream = line.split('\0', 1)
                if upstream == remote_ref:
                    return self.run('switch', '--', name.removeprefix('refs/heads/'))
            remote_name = next((name for name in sorted(self.remote_names(), key=len, reverse=True) if branch.startswith(name + '/')), None)
            local_name = branch[len(remote_name) + 1:] if remote_name else branch.split('/', 1)[-1]
            if self.run('show-ref', '--verify', 'refs/heads/' + local_name, check=False).strip():
                raise GitError('Local branch ' + local_name + ' already exists and tracks a different reference. Choose another local branch name.')
            return self.run("switch", "--track", "-c", local_name, "--", remote_ref)
        if remote_reference:
            raise GitError('Remote branch no longer exists: ' + branch)
        return self.run("switch", "--", branch)

    def diff(self, file: GitFile, staged: bool = False) -> str:
        if file.index == "?":
            path = self.directory / file.path
            if path.stat().st_size > 2_000_000:
                return "File is too large to preview."
            data = path.read_bytes()
            if b"\0" in data:
                return "Binary file."
            return data.decode("utf-8", errors="replace")
        return self.run("diff", "--no-ext-diff", "--no-textconv", *( ["--cached"] if staged else []),
                        "--", file.path, *( [file.original] if file.original else []))

    def remote_names(self) -> list[str]:
        return self.run("remote").splitlines()

    def publish(self, remote: str) -> str:
        branch = self.run("symbolic-ref", "--quiet", "--short", "HEAD").strip()
        return self.run("push", "--set-upstream", "--", remote, branch)

    def hunks(self, file: GitFile) -> list[str]:
        """Return self-contained patches for a modified tracked text file."""
        import re
        if file.conflicted or file.original or file.worktree != "M":
            raise GitError("Hunk staging requires a modified tracked text file.")
        patch = self.diff(file)
        matches = list(re.finditer(r"^@@ .*@@.*$", patch, flags=re.MULTILINE))
        if not matches:
            raise GitError("No text hunks available.")
        header = patch[:matches[0].start()]
        return [header + patch[match.start():matches[i + 1].start() if i + 1 < len(matches) else len(patch)]
                for i, match in enumerate(matches)]

    def stage_hunk(self, patch: str) -> str:
        return self.run("apply", "--cached", "--recount", "-", input_data=patch.encode("utf-8"))

    def history(self, limit: int = 200, skip: int = 0) -> tuple[GitCommit, ...]:
        output = self.run("log", "--all", "--topo-order", "-z",
                          "--format=%H%x00%P%x00%an%x00%aI%x00%D%x00%s",
                          f"--max-count={limit}", f"--skip={skip}")
        fields = output.split("\0")
        if fields and fields[-1] == "":
            fields.pop()
        return tuple(GitCommit(fields[i], tuple(fields[i + 1].split()), *fields[i + 2:i + 6])
                     for i in range(0, len(fields), 6))

    def commit_details(self, oid: str) -> str:
        import re
        if not re.fullmatch(r"[0-9a-f]{40,64}", oid):
            raise GitError("Invalid commit identifier.")
        return self.run("show", "--no-ext-diff", "--no-textconv", "--format=fuller",
                        "--stat", "--patch", oid, "--")

    def references(self) -> tuple[GitReference, ...]:
        fields = ("refname", "objectname", "objecttype", "symref", "authorname",
                  "committerdate:iso-strict", "subject", "upstream:short", "upstream:track",
                  "*authorname", "*committerdate:iso-strict", "*subject", "*objectname")
        output = self.run("for-each-ref", "--sort=-committerdate",
                          "--format=" + "%00".join("%(" + field + ")" for field in fields),
                          "refs/heads", "refs/remotes", "refs/tags")
        result = []
        for line in output.split("\n"):
            if not line:
                continue
            ref, oid, kind, symbolic, author, date, subject, upstream, tracking, tag_author, tag_date, tag_subject, tag_oid = line.split("\0")
            if symbolic:
                continue
            category, name = ("local", ref[11:]) if ref.startswith("refs/heads/") else ("remote", ref[13:]) if ref.startswith("refs/remotes/") else ("tag", ref[10:])
            result.append(GitReference(name, ref, category, tag_oid or oid, tag_author or author,
                                       tag_date or date, tag_subject or subject, upstream, tracking))
        return tuple(result)

    def create_branch(self, name: str, start: str | None = None, track: bool = False) -> str:
        self.run("check-ref-format", "--branch", name)
        if start:
            self.run("rev-parse", "--verify", "--end-of-options", start + "^{commit}")
            return self.run("switch", *(["--track"] if track else []), "-c", name, "--", start)
        return self.switch(name, create=True)

    def detach(self, reference: str) -> str:
        oid = self.run("rev-parse", "--verify", "--end-of-options", reference + "^{commit}").strip()
        return self.run("switch", "--detach", oid)

    def change_content(self, file: GitFile, staged: bool = False) -> tuple[str | None, str | None]:
        old_path = file.original or file.path
        if staged:
            before = self.run("show", "HEAD:" + old_path, check=False) or None
            after = self.run("show", ":" + file.path, check=False) or None
        else:
            before = self.run("show", ":" + file.path, check=False) or None
            path = self.directory / file.path
            after = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None
        return before, after


    def document_revision(self, project_path: str, revision: str):
        """Read a complete snapshot with two Git processes, regardless of object count."""
        from proteus.services.git_document import assemble_project
        prefix = Path(project_path).parent.as_posix()
        prefix = '' if prefix == '.' else prefix + '/'
        if revision == 'worktree':
            project = self.directory / project_path
            if not project.is_file():
                return None
            sources = [path.read_text(encoding='utf-8') for path in (self.directory / prefix / 'objects').rglob('*.xml')]
            return assemble_project(project.read_text(encoding='utf-8'), sources)
        if revision == 'HEAD':
            listing = self.run('ls-tree', '-r', '-z', 'HEAD', '--', project_path, prefix + 'objects/', check=False)
        elif revision == 'index':
            listing = self.run('ls-files', '--stage', '-z', '--', project_path, prefix + 'objects/')
        else:
            raise ValueError('Unknown Git document revision')
        entries = []
        for entry in listing.split('\0'):
            if not entry:
                continue
            metadata, path = entry.split('\t', 1)
            mode, second, third = metadata.split()
            oid = third if revision == 'HEAD' else second
            if revision == 'index' and third != '0':
                continue
            if mode == '120000' or not path.endswith('.xml'):
                continue
            entries.append((path, oid))
        if not any(path == project_path for path, _ in entries):
            return None
        payload = self.run('cat-file', '--batch', input_data=('\n'.join(oid for _, oid in entries) + '\n').encode('ascii'), binary=True)
        offset, contents = 0, {}
        for path, oid in entries:
            end = payload.index(b'\n', offset)
            header = payload[offset:end].split()
            if len(header) != 3 or header[1] != b'blob':
                raise GitError('Cannot read document snapshot: ' + path)
            size = int(header[2])
            offset = end + 1
            contents[path] = payload[offset:offset + size].decode('utf-8', errors='replace')
            offset += size + 1
        return assemble_project(contents.pop(project_path), contents.values())


    def pull_with_stash(self, flag: str, retained_message: str) -> str:
        """Restore the exact stash after a successful pull; preserve it on any failure."""
        if not self.status().files:
            return self.run('pull', flag)
        previous = self.run('rev-parse', '--verify', 'refs/stash', check=False).strip()
        self.run('stash', 'push', '--include-untracked', '-m', 'PROTEUS: changes before pull')
        oid = self.run('rev-parse', '--verify', 'refs/stash').strip()
        if not oid or oid == previous:
            raise GitError(retained_message)
        try:
            if self.status().files:
                raise GitError('Working tree is still modified.')
            output = self.run('pull', flag)
            self.run('stash', 'apply', '--index', oid)
        except GitError as error:
            raise GitError(str(error) + '\n\n' + retained_message) from error
        for line in self.run('stash', 'list', '--format=%gd:%H').splitlines():
            name, stored_oid = line.split(':', 1)
            if stored_oid == oid:
                self.run('stash', 'drop', name)
                break
        return output


    def worktrees(self) -> tuple[GitWorktree, ...]:
        output = self.run('worktree', 'list', '--porcelain', '-z')
        result = []
        fields = {}
        for field in output.split('\0'):
            if not field:
                if fields:
                    result.append(GitWorktree(fields['worktree'], fields.get('branch', '').removeprefix('refs/heads/'),
                                              fields.get('HEAD', ''), 'bare' in fields,
                                              fields.get('locked'), fields.get('prunable')))
                    fields = {}
            else:
                key, _, value = field.partition(' ')
                fields[key] = value
        return tuple(result)
