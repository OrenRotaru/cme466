from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from cv_pipeline_lab.core.registry import create_default_registry
from cv_pipeline_lab.ui.main_window import MainWindow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CV Pipeline Lab")
    parser.add_argument("--image", type=str, default=None, help="Override ImageInput path at run time")
    parser.add_argument("--pipeline", type=str, default=None, help="Open pipeline JSON on startup")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = QApplication(sys.argv)
    app.setApplicationName("CV Pipeline Lab")

    registry = create_default_registry()
    window = MainWindow(registry, image_override=args.image, pipeline_path=args.pipeline)
    window.show()

    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
