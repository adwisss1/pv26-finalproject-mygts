"""
Utils: Worker Thread
Jalankan fungsi berat (load data, export) di background thread
agar UI tidak freeze.

Cara pakai:
    self._worker = DataWorker(fungsi_load_data)
    self._worker.result.connect(self._on_data_loaded)
    self._worker.error.connect(self._on_error)
    self._worker.start()
"""

from PySide6.QtCore import QThread, Signal


class DataWorker(QThread):
    """
    Worker generik: jalankan callable di thread terpisah,
    emit 'result' dengan data kembalian, atau 'error' dengan pesan error.
    """
    result    = Signal(object)   # data apapun
    error     = Signal(str)      # pesan error
    finished  = Signal()         # signal ketika selesai

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self._func   = func
        self._args   = args
        self._kwargs = kwargs
        # Cleanup otomatis setelah selesai
        self.finished.connect(self.deleteLater)

    def run(self):
        try:
            data = self._func(*self._args, **self._kwargs)
            self.result.emit(data)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class ExportWorker(QThread):
    """
    Worker khusus export — emit 'done' dengan path file hasil export,
    atau 'error' dengan pesan error.
    """
    done  = Signal(str)   # path file
    error = Signal(str)

    def __init__(self, export_func, data, title="Laporan MyGTS", filename=None):
        super().__init__()
        self._func     = export_func
        self._data     = data
        self._title    = title
        self._filename = filename

    def run(self):
        try:
            # Cek apakah fungsi butuh parameter title (PDF) atau tidak (CSV)
            import inspect
            sig = inspect.signature(self._func)
            params = list(sig.parameters.keys())
            if "title" in params:
                path = self._func(self._data, title=self._title,
                                  filename=self._filename)
            else:
                path = self._func(self._data, filename=self._filename)
            self.done.emit(path)
        except Exception as e:
            self.error.emit(str(e))