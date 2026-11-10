import logging
import multiprocessing
from queue import Empty
from concurrent.futures import ProcessPoolExecutor
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    """Signals to ship data back across thread/process boundaries."""
    finished = Signal(object)
    updated = Signal(object)


class ThreadWorker(QRunnable):
    """Handles thread-based tasks. Allows passing an update_callback directly."""
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


class ProcessWorker(QRunnable):
    """Handles process-based tasks and bridges cross-process queues to Qt signals."""
    def __init__(
        self,
        executor,
        function,
        *args,
        enable_updates=False,
        **kwargs
    ):
        super().__init__()
        self.executor = executor
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        self._manager = (
            multiprocessing.Manager() if enable_updates else None
        )

        self.queue = (
            self._manager.Queue()
            if self._manager is not None
            else None
        )

    @Slot()
    def run(self):
        try:
            future = self.executor.submit(self.function, *self.args, **self.kwargs)
            if self.queue is not None:
                while not future.done():
                    try:
                        update_data = self.queue.get(timeout=0.05)
                        self.signals.updated.emit(update_data)

                    except Empty:
                        pass

                while True:
                    try:
                        update_data = self.queue.get_nowait()
                        self.signals.updated.emit(update_data)

                    except Empty:
                        break

            result = future.result()

        except Exception as error:
            result = error

        finally:
            try:
                if self._manager is not None:
                    self._manager.shutdown()

            except Exception:
                logger.exception("Failed to shut down ProcessWorker manager.")

            self.signals.finished.emit(result)


_PROCESS_POOL = None

def get_process_pool():
    global _PROCESS_POOL

    if _PROCESS_POOL is None:
        _PROCESS_POOL = ProcessPoolExecutor()

    return _PROCESS_POOL


def run_in_background(
    function,
    *args,
    on_complete=None,
    on_update=None,
    mode="thread",
    **kwargs
):
    """Unified execution manager with live updating."""
    if mode == "process":
        executor = get_process_pool()

        worker = ProcessWorker(
            executor,
            function,
            *args,
            enable_updates=on_update is not None,
            **kwargs
        )

        if on_update is not None:
            worker.kwargs["update_queue"] = worker.queue

    else:
        worker = ThreadWorker(function, *args, **kwargs)
        if on_update is not None:
            worker.kwargs["update_callback"] = (
                worker.signals.updated.emit
            )

    if on_complete is not None:
        worker.signals.finished.connect(on_complete)

    if on_update is not None:
        worker.signals.updated.connect(on_update)

    QThreadPool.globalInstance().start(worker)

def shutdown_process_pool() -> None:
    """Terminate active process workers during application shutdown."""

    global _PROCESS_POOL

    if _PROCESS_POOL is None:
        return

    logger.info("Killing active process workers.")

    try:
        _PROCESS_POOL.kill_workers()
    finally:
        _PROCESS_POOL = None

    logger.info("Process pool shutdown requested.")