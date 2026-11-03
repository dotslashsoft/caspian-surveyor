from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

class WorkerSignals(QObject):
    finished = Signal(object)

class BackgroundWorker(QRunnable):
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            result = self.function(*self.args, **self.kwargs)
        except Exception as error:
            result = error
        finally:
            self.signals.finished.emit(result)

def run_in_background(function, *args, on_complete=None, **kwargs):
    worker_thread = BackgroundWorker(function, *args, **kwargs)

    if on_complete is not None:
        worker_thread.signals.finished.connect(on_complete)

    QThreadPool.globalInstance().start(worker_thread)