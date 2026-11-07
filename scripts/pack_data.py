"""Package only public source/data artifacts; never environment files or secrets."""

import tarfile

from climate.config import ROOT, settings
from climate.files import active_release


def main():
    release_id, release = active_release()
    target = ROOT / "data/bootstrap-release.tar.gz"
    entries = [
        settings.data_dir / "active.json",
        release,
        settings.data_dir / "assets",
        settings.data_dir / "imagery",
        settings.raw_dir / "archive-inventory.json",
        settings.raw_dir / "power",
        settings.raw_dir / "gistemp",
        settings.raw_dir / "gazetteer",
        settings.raw_dir / "imagery-metadata",
        ROOT / "data/manifests",
    ]
    with tarfile.open(target, "w:gz", compresslevel=6) as archive:
        for path in entries:
            if path.exists():
                archive.add(path, arcname=str(path.relative_to(ROOT / "data")))
    print(f"Packaged {release_id}: {target.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
