"""Restore the shipped, public, reviewed snapshot without replacing active data."""

import tarfile

from climate.config import ROOT, settings


def main():
    if (settings.data_dir / "active.json").exists():
        print("Existing prepared data preserved.")
        return
    archive = ROOT / "data/bootstrap-release.tar.gz"
    if not archive.exists():
        from pipelines.build import build_release, import_archive

        import_archive()
        build_release()
        print("Numerical data prepared. Run imagery acquisition to complete image stories.")
        return
    target = ROOT / "data"
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as handle:
        for member in handle.getmembers():
            if member.issym() or member.islnk():
                raise ValueError("Bootstrap snapshot contains an unexpected link")
        handle.extractall(target, filter="data")
    print("Reviewed public data snapshot restored.")


if __name__ == "__main__":
    main()
