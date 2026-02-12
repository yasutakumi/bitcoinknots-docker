#!/usr/bin/env python3
"""
CI helper script for bitcoinknots-docker builds.

Commands:
    matrix <--ref REF>       Output build matrix as JSON for GitHub Actions
    tags <--version V>       Output Docker tags for a version
    should-push <--ref REF>  Check if images should be pushed (true/false)
"""

import argparse
import json
import re
import sys
from pathlib import Path


class Version:
    """Parsed version with comparison support."""

    def __init__(self, version_str: str):
        self.original = version_str
        self.major = 0
        self.minor = 0
        self.patch = None
        self.rc = None
        self.fork = ""
        self.fork_major = 0
        self.fork_minor = 0
        self.fork_patch = 0

        match = re.match(
            r"^(\d+)\.(\d+)(?:\.([a-z0-9]+?))?(?:\+([^-]+)-v(\d+)\.(\d+)(?:\.(\d+))?)?(?:rc(\d+))?$",
            version_str,
        )
        if not match:
            raise ValueError(f"Invalid version format: {version_str}")

        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self.patch = match.group(3) if match.group(3) else None
        self.fork = match.group(4) if match.group(4) else ""
        self.fork_major = int(match.group(5)) if match.group(5) else 0
        self.fork_minor = int(match.group(6)) if match.group(6) else 0
        self.fork_patch = int(match.group(7)) if match.group(7) else 0
        self.rc = int(match.group(8)) if match.group(8) else None

    def __str__(self):
        return self.original

    def __lt__(self, other):
        if self.base != other.base:
            return self.base < other.base
        if self.fork != other.fork:
            return self.fork < other.fork
        self_tuple = (self.major, self.minor, self.patch_num)
        other_tuple = (other.major, other.minor, other.patch_num)
        if self_tuple != other_tuple:
            return self_tuple < other_tuple
        self_fork_tuple = (self.fork_major, self.fork_minor, self.fork_patch)
        other_fork_tuple = (other.fork_major, other.fork_minor, other.fork_patch)
        if self_fork_tuple != other_fork_tuple:
            return self_fork_tuple < other_fork_tuple
        if self.rc is None and other.rc is None:
            return False
        if self.rc is None:
            return False
        if other.rc is None:
            return True
        return self.rc < other.rc

    def __eq__(self, other):
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.rc == other.rc
            and self.fork == other.fork
            and self.fork_major == other.fork_major
            and self.fork_minor == other.fork_minor
            and self.fork_patch == other.fork_patch
        )

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return not self < other

    @property
    def patch_num(self):
        if self.patch is None:
            return 0
        if match := re.match(r"^knots(\d+)$", self.patch):
            return int(match.group(1))
        return 0

    @property
    def base(self):
        if self.patch is None:
            return "core"
        if re.match(r"^knots", self.patch):
            return "knots"
        return "core"

    @property
    def is_rc(self):
        return self.rc is not None

    @property
    def is_fork(self):
        return self.fork != ""

    @property
    def fork_version(self):
        if not self.is_fork:
            return ""
        return f"{self.fork}-v{self.fork_major}.{self.fork_minor}" + (
            f".{self.fork_patch}" if self.fork_patch != 0 else ""
        )


def get_repo_root() -> Path:
    """Find repository root (directory containing .github)."""
    repo_root = Path(__file__).parent.parent
    if not (repo_root / ".github").exists():
        print("Error: Could not find repository root", file=sys.stderr)
        sys.exit(1)
    return repo_root


def discover_versions(repo_root: Path) -> list[str]:
    """Find all top-level version directories (excluding deprecated, master, scripts)."""
    exclude = {"deprecated", "master", "scripts", ".github"}
    versions = []
    for path in repo_root.iterdir():
        if not path.is_dir():
            continue
        if path.name.startswith("."):
            continue
        if path.name in exclude:
            continue
        if (path / "Dockerfile").exists():
            try:
                Version(path.name)
                versions.append(path.name)
            except ValueError:
                continue
    return versions


def discover_all_top_level(repo_root: Path) -> list[str]:
    """Find all top-level directories with Dockerfiles (including master)."""
    exclude = {"deprecated", "scripts", ".github"}
    dirs = []
    for path in repo_root.iterdir():
        if not path.is_dir():
            continue
        if path.name.startswith("."):
            continue
        if path.name in exclude:
            continue
        if (path / "Dockerfile").exists():
            dirs.append(path.name)
    return dirs


def get_latest_version(
    repo_root: Path,
    *,
    base: str | None = None,
    fork: str | None = None,
    major: int | None = None,
    minor: int | None = None,
) -> Version | None:
    """Get the highest non-RC version."""
    versions = []
    for v_str in discover_versions(repo_root):
        try:
            v = Version(v_str)
            if base is not None and v.base != base:
                continue
            if fork is not None and v.fork != fork:
                continue
            if major is not None and v.major != major:
                continue
            if minor is not None and v.minor != minor:
                continue
            if not v.is_rc:
                versions.append(v)
        except ValueError:
            continue
    return max(versions) if versions else None


def get_matrix(github_ref: str, repo_root: Path, version: str | None = None) -> dict:
    """Generate build matrix based on GitHub ref or explicit version."""
    if version:
        version_dir = repo_root / version
        if not version_dir.is_dir():
            print(f"Error: Directory '{version}' does not exist", file=sys.stderr)
            sys.exit(1)
        dirs = [version]
    elif github_ref.startswith("refs/tags/v"):
        tag_version = github_ref.removeprefix("refs/tags/v")
        version_dir = repo_root / tag_version
        if not version_dir.is_dir():
            print(
                f"Error: Directory '{tag_version}' does not exist for tag",
                file=sys.stderr,
            )
            sys.exit(1)
        dirs = [tag_version]
    else:
        dirs = discover_all_top_level(repo_root)

    include = []
    for d in sorted(dirs):
        include.append({"version": d, "variant": "debian"})
        alpine_dir = repo_root / d / "alpine"
        if alpine_dir.is_dir() and (alpine_dir / "Dockerfile").exists():
            include.append({"version": d, "variant": "alpine"})

    return {"include": include}


def format_tag(repo: str, tag: str) -> str:
    """Format a Docker tag."""
    formatted_tag = re.sub(r"[^a-zA-Z0-9._-]", "-", tag)
    return f"{repo}:{formatted_tag}"


def generate_tags(
    version_str: str, alpine: bool, repo_root: Path, *, repo: str
) -> list[str]:
    """Generate Docker tags for a version.

    Preserves the tag logic from the original build.yml.
    """
    tags: list[str] = []
    alpine_suffix = "-alpine" if alpine else ""

    if version_str == "master":
        tags.append(format_tag(repo, f"master{alpine_suffix}"))
        return tags

    try:
        v = Version(version_str)
    except ValueError:
        return [format_tag(repo, f"{version_str}{alpine_suffix}")]

    latest = get_latest_version(repo_root, base=v.base, fork=v.fork)
    latest_for_major = get_latest_version(
        repo_root, base=v.base, fork=v.fork, major=v.major
    )
    latest_for_major_minor = get_latest_version(
        repo_root,
        base=v.base,
        fork=v.fork,
        major=v.major,
        minor=v.minor,
    )

    major_tag, minor_tag, patch_tag, rc_tag = None, None, None, None
    fork_suffix = f"-{v.fork_version}" if v.is_fork else ""
    if not v.is_rc:
        if not v.is_fork:
            major_tag = f"{v.major}"
            minor_tag = f"{v.major}.{v.minor}"
        patch_tag = (
            f"{v.major}.{v.minor}.{v.patch}{fork_suffix}"
            if v.patch is not None
            else None
        )
    else:
        rc_tag = (
            f"{v.major}.{v.minor}.{v.patch}{fork_suffix}rc{v.rc}"
            if v.patch is not None
            else f"{v.major}.{v.minor}{fork_suffix}rc{v.rc}"
        )

    if rc_tag is not None:
        tags.append(format_tag(repo, f"{rc_tag}{alpine_suffix}"))
    if patch_tag is not None:
        tags.append(format_tag(repo, f"{patch_tag}{alpine_suffix}"))
    if minor_tag is not None and (
        not latest or latest_for_major_minor is None or v >= latest_for_major_minor
    ):
        tags.append(format_tag(repo, f"{minor_tag}{alpine_suffix}"))
    if major_tag is not None and (
        not latest or latest_for_major is None or v >= latest_for_major
    ):
        tags.append(format_tag(repo, f"{major_tag}{alpine_suffix}"))

    if v.base == "knots" and not v.is_fork and not v.is_rc and latest and v >= latest:
        if not alpine:
            if f"{repo}:latest" not in tags:
                tags.append(format_tag(repo, "latest"))
            if major_tag is not None and f"{repo}:{major_tag}" not in tags:
                tags.append(format_tag(repo, major_tag))
        else:
            if f"{repo}:alpine" not in tags:
                tags.append(format_tag(repo, "alpine"))
            if (
                major_tag is not None
                and f"{repo}:{major_tag}{alpine_suffix}" not in tags
            ):
                tags.append(format_tag(repo, f"{major_tag}{alpine_suffix}"))

    return tags


def should_push(github_ref: str, version: str | None = None) -> bool:
    """Determine if images should be pushed."""
    if version:
        return version != "master"
    if not github_ref.startswith("refs/tags/v"):
        return False
    tag_version = github_ref.removeprefix("refs/tags/v")
    return tag_version != "master"


def cmd_matrix(args):
    """Handle 'matrix' command."""
    repo_root = get_repo_root()
    matrix = get_matrix(args.ref, repo_root, getattr(args, "version", None))
    print(json.dumps(matrix, separators=(",", ":")))


def cmd_tags(args):
    """Handle 'tags' command."""
    repo_root = get_repo_root()
    tags = generate_tags(args.version, args.alpine, repo_root, repo=args.repo)
    print(" ".join(tags))


def cmd_should_push(args):
    """Handle 'should-push' command."""
    result = should_push(args.ref, getattr(args, "version", None))
    print("true" if result else "false")


def main():
    parser = argparse.ArgumentParser(
        description="CI helper for bitcoinknots-docker builds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    matrix_parser = subparsers.add_parser("matrix", help="Output build matrix as JSON")
    matrix_parser.add_argument(
        "--ref",
        required=True,
        help="GitHub ref (e.g., refs/tags/v30.2, refs/heads/master)",
    )
    matrix_parser.add_argument(
        "--version",
        help="Override: build only this version (e.g., 30.2)",
    )

    tags_parser = subparsers.add_parser("tags", help="Output Docker tags for a version")
    tags_parser.add_argument(
        "--version", required=True, help="Version (e.g., 30.2, master)"
    )
    tags_parser.add_argument(
        "--alpine", action="store_true", help="Generate alpine tags"
    )
    tags_parser.add_argument(
        "--repo",
        default="bitcoinknots/bitcoin",
        help="Docker repo (default: %(default)s)",
    )

    push_parser = subparsers.add_parser(
        "should-push", help="Check if should push images"
    )
    push_parser.add_argument(
        "--ref",
        required=True,
        help="GitHub ref (e.g., refs/tags/v30.2, refs/heads/master)",
    )
    push_parser.add_argument(
        "--version",
        help="Override: if set, will push this version (e.g., 30.2)",
    )

    args = parser.parse_args()

    if args.command == "matrix":
        cmd_matrix(args)
    elif args.command == "tags":
        cmd_tags(args)
    elif args.command == "should-push":
        cmd_should_push(args)


if __name__ == "__main__":
    main()
