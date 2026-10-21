#!/usr/bin/env python3

import argparse
import re
from pathlib import Path

import requests


class GitHubRepoDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": "repo-downloader",
            }
        )

    def parse_repo_url(self, repo_url):
        pattern = r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)"

        match = re.match(pattern, repo_url)

        if not match:
            raise ValueError("Invalid GitHub repository URL")

        owner = match.group("owner")
        repo = match.group("repo").replace(".git", "")

        return owner, repo

    def get_default_branch(self, owner, repo):
        url = f"https://api.github.com/repos/{owner}/{repo}"

        response = self.session.get(url)
        response.raise_for_status()

        return response.json()["default_branch"]

    def download_file(self, file_url, local_path):
        local_path.parent.mkdir(parents=True, exist_ok=True)

        response = self.session.get(file_url, stream=True)
        response.raise_for_status()

        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print(f"Downloaded: {local_path}")

    def download_directory(
        self,
        owner,
        repo,
        ref,
        current_path,
        root_path,
        original_path,
    ):
        api_url = (
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/contents/{current_path}"
            f"?ref={ref}"
        )

        response = self.session.get(api_url)
        response.raise_for_status()

        items = response.json()

        if isinstance(items, dict):
            items = [items]

        for item in items:
            if item["type"] == "file":

                repo_file_path = Path(item["path"])

                if original_path:
                    relative_path = repo_file_path.relative_to(original_path)
                else:
                    relative_path = repo_file_path

                local_path = root_path / relative_path

                self.download_file(
                    item["download_url"],
                    local_path,
                )

            elif item["type"] == "dir":
                self.download_directory(
                    owner,
                    repo,
                    ref,
                    item["path"],
                    root_path,
                    original_path,
                )

    def download_repo(
        self,
        repo_url,
        path=None,
        ref=None,
    ):
        owner, repo = self.parse_repo_url(repo_url)

        if not ref:
            ref = self.get_default_branch(owner, repo)

        outputs = Path("outputs")

        if path:
            target_root = outputs / Path(path).name

            print(
                f"Downloading '{path}' "
                f"from {owner}/{repo}@{ref}"
            )

            self.download_directory(
                owner,
                repo,
                ref,
                path,
                target_root,
                path,
            )

        else:
            target_root = outputs / repo

            print(
                f"Downloading repository "
                f"{owner}/{repo}@{ref}"
            )

            self.download_directory(
                owner,
                repo,
                ref,
                "",
                target_root,
                "",
            )

        print(f"\nFinished.")
        print(f"Saved to: {target_root}")


def main():
    parser = argparse.ArgumentParser(
        description="Download GitHub repositories or folders"
    )

    parser.add_argument(
        "repo_url",
        help="GitHub repository URL",
    )

    parser.add_argument(
        "--path",
        help="Subdirectory inside repository",
        default=None,
    )

    parser.add_argument(
        "--ref",
        help="Branch, tag, or commit SHA",
        default=None,
    )

    args = parser.parse_args()

    downloader = GitHubRepoDownloader()

    downloader.download_repo(
        repo_url=args.repo_url,
        path=args.path,
        ref=args.ref,
    )


if __name__ == "__main__":
    main()