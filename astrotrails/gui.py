# SPDX-License-Identifier: GPL-3.0-or-later
"""PyQt6 GUI for astrotrails.

The stacking pipeline runs in a ``QThread`` subclass; the main thread only
updates widgets from signal handlers, keeping Qt happy.  Cancellation uses a
``threading.Event`` checked between frames.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

from PIL import Image
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .core import (
    StackMode,
    StackParams,
    list_images,
    load_dark_frame,
    save_image,
    stack_frames,
)
from .video import FFmpegNotFound, FFmpegPipeWriter

# ------------------------------------------------------------------ styling ---

def _check_svg_uri() -> str:
    """Return an absolute path to the bundled check.svg asset, in QSS-friendly form.

    Qt's QSS accepts plain absolute paths in url(...) — and unlike url(file:///...)
    this works consistently across platforms.  Forward slashes are accepted on
    Windows too; backslashes confuse the QSS parser.
    """
    asset = Path(__file__).parent / "assets" / "check.svg"
    return asset.resolve().as_posix()


_AWESOME_DARK_QSS_TEMPLATE = """
QWidget {
    background-color: #1e2228;
    color: #d7dce2;
    font-family: Consolas, "Courier New", monospace;
    font-size: 11pt;
}
QMainWindow, QSplitter, QGroupBox { background-color: #1e2228; }
QGroupBox {
    border: 1px solid #3a4049;
    border-radius: 2px;
    margin-top: 14px;
    padding: 10px 8px 6px 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #6bb8c9;
    font-weight: 600;
    letter-spacing: 1px;
}
QLineEdit, QComboBox, QSpinBox, QTextEdit {
    background-color: #2a2f36;
    border: 1px solid #3a4049;
    border-radius: 2px;
    padding: 4px 6px;
    selection-background-color: #6bb8c9;
    selection-color: #1e2228;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {
    border: 1px solid #6bb8c9;
}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {
    color: #5a6068;
    background-color: #23272d;
}
QPushButton {
    background-color: transparent;
    color: #6bb8c9;
    border: 1px solid #6bb8c9;
    border-radius: 2px;
    padding: 6px 14px;
    font-weight: 600;
}
QPushButton:hover { background-color: #6bb8c9; color: #1e2228; }
QPushButton:pressed { background-color: #4fa2b3; }
QPushButton:disabled { color: #4a5058; border-color: #3a4049; }
QPushButton#danger { color: #e8b84b; border-color: #e8b84b; }
QPushButton#danger:hover { background-color: #e8b84b; color: #1e2228; }
QPushButton#danger:disabled {
    color: #4a5058;
    border-color: #3a4049;
    background-color: transparent;
}
QLabel#heading {
    color: #6bb8c9;
    font-size: 18pt;
    font-weight: 600;
    letter-spacing: 4px;
}
QLabel#subheading { color: #8a9099; font-size: 9pt; letter-spacing: 1px; }
QProgressBar {
    background-color: #2a2f36;
    border: 1px solid #3a4049;
    border-radius: 2px;
    text-align: center;
    color: #d7dce2;
    height: 20px;
}
QProgressBar::chunk { background-color: #6bb8c9; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background-color: #2a2f36;
    border: 1px solid #6bb8c9;
    selection-background-color: #6bb8c9;
    selection-color: #1e2228;
}
QCheckBox { spacing: 8px; }
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #6bb8c9;
    background-color: transparent;
    border-radius: 2px;
}
QCheckBox::indicator:checked {
    background-color: transparent;
    image: url(__CHECK_SVG__);
}
QCheckBox::indicator:disabled {
    border-color: #3a4049;
}
"""


def awesome_dark_qss() -> str:
    """Return the assembled stylesheet with the checkmark SVG path baked in."""
    return _AWESOME_DARK_QSS_TEMPLATE.replace("__CHECK_SVG__", _check_svg_uri())


# ------------------------------------------------------------------ worker ---

class StackingWorker(QThread):
    """Background stacker.  Communicates with the GUI via signals."""

    progress = pyqtSignal(int, int)
    log = pyqtSignal(str)
    finished_ok = pyqtSignal(str, str)  # (image_path, video_path) — empty string if not produced
    failed = pyqtSignal(str)

    def __init__(self, params: dict[str, object]) -> None:
        super().__init__()
        self._params = params
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    def run(self) -> None:  # noqa: C901 — mostly linear, reads top-to-bottom
        try:
            input_dir: Path = self._params["input_dir"]  # type: ignore[assignment]
            output_dir: Path = self._params["output_dir"]  # type: ignore[assignment]
            make_image: bool = bool(self._params["make_image"])
            make_video: bool = bool(self._params["make_video"])

            self.log.emit(f"scanning {input_dir}")
            images = list_images(input_dir)
            if not images:
                raise RuntimeError("no supported images found in input directory")
            self.log.emit(f"found {len(images)} images")

            dark = None
            df: Path | None = self._params.get("dark_frame")  # type: ignore[assignment]
            if df is not None:
                self.log.emit(f"loading dark frame {df.name}")
                dark = load_dark_frame(df)

            params = StackParams(
                mode=StackMode(self._params["mode"]),
                comet_length=int(self._params["comet_length"]),
                dark_frame=dark,
                workers=int(self._params["workers"]),
            )
            self.log.emit(
                f"mode={params.mode.value} workers={params.workers} "
                + (f"comet_length={params.comet_length}"
                   if params.mode is StackMode.COMET else "")
            )

            output_dir.mkdir(parents=True, exist_ok=True)
            image_out = output_dir / str(self._params["image_name"])
            video_out = output_dir / str(self._params["video_name"])
            image_path = ""
            video_path = ""

            def on_progress(cur: int, tot: int) -> None:
                self.progress.emit(cur, tot)

            with Image.open(images[0]) as im:
                width, height = im.size

            last_frame = None
            if make_video:
                self.log.emit(
                    f"piping {len(images)} frames → ffmpeg @ {self._params['fps']}fps"
                )
                try:
                    writer_ctx = FFmpegPipeWriter(
                        video_out, width, height,
                        fps=int(self._params["fps"]),  # type: ignore[arg-type]
                    )
                except FFmpegNotFound as e:
                    raise RuntimeError(str(e)) from e

                with writer_ctx as writer:
                    for frame in stack_frames(images, params=params,
                                              progress=on_progress, cancel=self._cancel):
                        writer.write_frame(frame)
                        last_frame = frame
                video_path = str(video_out)
            else:
                for frame in stack_frames(images, params=params,
                                          progress=on_progress, cancel=self._cancel):
                    last_frame = frame

            if make_image and last_frame is not None:
                self.log.emit(f"saving {image_out.name}")
                save_image(last_frame, image_out, exif_source=images[0])
                image_path = str(image_out)

            self.finished_ok.emit(image_path, video_path)

        except Exception as e:  # noqa: BLE001 — GUI needs to report anything
            self.failed.emit(str(e))


# ------------------------------------------------------------------ window ---

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Astrotrails")
        self.resize(1000, 720)
        self._worker: StackingWorker | None = None
        self._build_ui()
        self.setStyleSheet(awesome_dark_qss())

    # -- UI construction --------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # Split: controls left, log + preview right.
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._controls_panel())
        splitter.addWidget(self._output_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([420, 580])
        root.addWidget(splitter, 1)

        # Progress + action buttons.
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFormat("idle")
        root.addWidget(self.progress_bar)

        self.generate_btn = QPushButton("Generate")
        self.generate_btn.clicked.connect(self._on_generate)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("danger")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)

        btns = QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.generate_btn)
        root.addLayout(btns)

    def _controls_panel(self) -> QWidget:
        wrap = QWidget()
        layout = QVBoxLayout(wrap)
        layout.setSpacing(10)

        # --- paths -------------------------------------------------------
        paths_box = QGroupBox("PATHS")
        paths = QFormLayout(paths_box)
        paths.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("folder of night-sky JPEGs / TIFFs")
        paths.addRow("Input:", self._path_row(self.input_edit, self._pick_input))

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("defaults to input directory")
        paths.addRow("Output:", self._path_row(self.output_edit, self._pick_output))

        self.dark_edit = QLineEdit()
        self.dark_edit.setPlaceholderText("optional dark frame image")
        paths.addRow("Dark frame:", self._path_row(self.dark_edit, self._pick_dark_frame))

        layout.addWidget(paths_box)

        # --- stacking ----------------------------------------------------
        stack_box = QGroupBox("STACKING")
        stack_f = QFormLayout(stack_box)
        stack_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Max (classic)", StackMode.MAX.value)
        self.mode_combo.addItem("Comet (fade tail)", StackMode.COMET.value)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        stack_f.addRow("Mode:", self.mode_combo)

        self.comet_spin = QSpinBox()
        self.comet_spin.setRange(2, 5000)
        self.comet_spin.setValue(50)
        self.comet_spin.setSuffix(" frames")
        self.comet_spin.setEnabled(False)
        stack_f.addRow("Comet tail:", self.comet_spin)

        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 32)
        self.workers_spin.setValue(4)
        stack_f.addRow("Decoder threads:", self.workers_spin)

        layout.addWidget(stack_box)

        # --- output ------------------------------------------------------
        out_box = QGroupBox("OUTPUT")
        out_f = QFormLayout(out_box)
        out_f.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.image_cb = QCheckBox("Stacked image")
        self.image_cb.setChecked(True)
        self.video_cb = QCheckBox("Timelapse video")
        self.video_cb.setChecked(True)
        row = QHBoxLayout()
        row.addWidget(self.image_cb)
        row.addWidget(self.video_cb)
        row.addStretch(1)
        out_f.addRow("Produce:", self._wrap(row))

        self.image_name_edit = QLineEdit("Stacked.jpg")
        out_f.addRow("Image name:", self.image_name_edit)
        self.video_name_edit = QLineEdit("timelapse.mp4")
        out_f.addRow("Video name:", self.video_name_edit)

        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 120)
        self.fps_spin.setValue(25)
        out_f.addRow("Video FPS:", self.fps_spin)

        layout.addWidget(out_box)
        layout.addStretch(1)
        return wrap

    def _output_panel(self) -> QWidget:
        wrap = QWidget()
        layout = QVBoxLayout(wrap)
        layout.setSpacing(8)

        # Preview goes on top, no group-box header — the image speaks for itself.
        preview_wrap = QWidget()
        prev_l = QVBoxLayout(preview_wrap)
        prev_l.setContentsMargins(0, 0, 0, 0)
        self.preview_label = QLabel("Generated image will appear here")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(220)
        self.preview_label.setStyleSheet(
            "color:#5a6068; border:1px solid #3a4049; border-radius:2px;"
        )
        prev_l.addWidget(self.preview_label)
        layout.addWidget(preview_wrap, 1)

        log_box = QGroupBox("LOG")
        log_l = QVBoxLayout(log_box)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        log_l.addWidget(self.log_view)
        layout.addWidget(log_box, 1)

        return wrap

    # -- small helpers ----------------------------------------------------

    def _wrap(self, layout: QHBoxLayout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

    def _path_row(self, edit: QLineEdit, picker) -> QWidget:
        wrap = QWidget()
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edit, 1)
        btn = QPushButton("…")
        btn.setFixedWidth(32)
        btn.clicked.connect(picker)
        layout.addWidget(btn)
        return wrap

    def _log(self, msg: str) -> None:
        self.log_view.append(msg)

    # -- slots ------------------------------------------------------------

    def _pick_input(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Select input directory")
        if d:
            self.input_edit.setText(d)
            if not self.output_edit.text().strip():
                self.output_edit.setText(d)

    def _pick_output(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Select output directory")
        if d:
            self.output_edit.setText(d)

    def _pick_dark_frame(self) -> None:
        f, _ = QFileDialog.getOpenFileName(
            self, "Select dark frame",
            filter="Images (*.jpg *.jpeg *.tif *.tiff *.png)",
        )
        if f:
            self.dark_edit.setText(f)

    def _on_mode_changed(self) -> None:
        is_comet = self.mode_combo.currentData() == StackMode.COMET.value
        self.comet_spin.setEnabled(is_comet)

    def _on_generate(self) -> None:
        input_dir = self.input_edit.text().strip()
        if not input_dir or not Path(input_dir).is_dir():
            QMessageBox.warning(self, "Input", "Choose a valid input directory.")
            return
        if not (self.image_cb.isChecked() or self.video_cb.isChecked()):
            QMessageBox.warning(self, "Output", "Select at least one output type.")
            return

        dark_text = self.dark_edit.text().strip()
        dark_path = Path(dark_text) if dark_text else None
        if dark_path is not None and not dark_path.is_file():
            QMessageBox.warning(self, "Dark frame", "Dark frame file not found.")
            return

        params = {
            "input_dir": Path(input_dir),
            "output_dir": Path(self.output_edit.text().strip() or input_dir),
            "dark_frame": dark_path,
            "mode": self.mode_combo.currentData(),
            "comet_length": self.comet_spin.value(),
            "workers": self.workers_spin.value(),
            "make_image": self.image_cb.isChecked(),
            "make_video": self.video_cb.isChecked(),
            "image_name": self.image_name_edit.text().strip() or "Stacked.jpg",
            "video_name": self.video_name_edit.text().strip() or "timelapse.mp4",
            "fps": self.fps_spin.value(),
        }

        self.log_view.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("starting…")
        self._set_running(True)

        self._worker = StackingWorker(params)
        self._worker.progress.connect(self._on_progress)
        self._worker.log.connect(self._log)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_cancel(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._log("cancelling…")
            self._worker.cancel()

    @pyqtSlot(int, int)
    def _on_progress(self, cur: int, tot: int) -> None:
        pct = int(cur * 100 / tot) if tot else 0
        self.progress_bar.setValue(pct)
        self.progress_bar.setFormat(f"{cur} / {tot}  ({pct}%)")

    @pyqtSlot(str, str)
    def _on_finished(self, image_path: str, video_path: str) -> None:
        msg_parts = []
        if image_path:
            msg_parts.append(f"image → {image_path}")
        if video_path:
            msg_parts.append(f"video → {video_path}")
        self._log("done: " + " | ".join(msg_parts))
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("done")
        self._set_running(False)

        if image_path:
            pix = QPixmap(image_path)
            if not pix.isNull():
                scaled = pix.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.preview_label.setPixmap(scaled)

    @pyqtSlot(str)
    def _on_failed(self, message: str) -> None:
        self._log(f"ERROR: {message}")
        self.progress_bar.setFormat("failed")
        self._set_running(False)
        QMessageBox.critical(self, "Failed", message)

    def _set_running(self, running: bool) -> None:
        self.generate_btn.setEnabled(not running)
        self.cancel_btn.setEnabled(running)
        for w in (self.input_edit, self.output_edit, self.dark_edit,
                  self.mode_combo, self.workers_spin,
                  self.image_cb, self.video_cb,
                  self.image_name_edit, self.video_name_edit, self.fps_spin):
            w.setEnabled(not running)
        self.comet_spin.setEnabled(
            (not running) and self.mode_combo.currentData() == StackMode.COMET.value
        )


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("astrotrails")
    app.setApplicationVersion(__version__)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
