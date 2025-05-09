"""
File system monitoring for detecting file changes
"""
import os
import time
import threading
import logging
from typing import List, Dict, Any, Callable, Set
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from .extractors import extract_file_content

logger = logging.getLogger(__name__)

class FileMonitor:
    """Monitor file system changes and process files"""
    
    def __init__(self, 
                 watch_folders: List[str], 
                 on_file_added: Callable[[str], None],
                 on_file_modified: Callable[[str], None],
                 on_file_deleted: Callable[[str], None],
                 file_extensions: Set[str] = None):
        """
        Initialize the file monitor
        
        Args:
            watch_folders: List of folders to monitor
            on_file_added: Callback when a file is added
            on_file_modified: Callback when a file is modified
            on_file_deleted: Callback when a file is deleted
            file_extensions: Set of file extensions to monitor (None for all)
        """
        self.watch_folders = [Path(folder).resolve() for folder in watch_folders]
        self.on_file_added = on_file_added
        self.on_file_modified = on_file_modified
        self.on_file_deleted = on_file_deleted
        self.file_extensions = file_extensions
        
        self.observer = None
        self.stopped = threading.Event()
        self.lock = threading.RLock()
        
        # Keep track of processing files to avoid duplicate events
        self.processing_files = set()
    
    def _is_valid_file(self, path: str) -> bool:
        """Check if the file should be processed"""
        if not os.path.isfile(path):
            return False
        
        if self.file_extensions is not None:
            ext = os.path.splitext(path)[1].lower()
            return ext in self.file_extensions
        
        return True
    
    def _is_in_watched_folders(self, path: str) -> bool:
        """Check if the path is in one of the watched folders"""
        path = Path(path).resolve()
        for folder in self.watch_folders:
            try:
                path.relative_to(folder)
                return True
            except ValueError:
                continue
        return False
    
    def start(self) -> None:
        """Start monitoring"""
        with self.lock:
            if self.observer is not None:
                logger.warning("File monitor is already running")
                return
            
            # Create and start the observer
            self.observer = Observer()
            
            # Set up handlers for each watch folder
            for folder in self.watch_folders:
                if not folder.exists():
                    logger.warning(f"Watch folder does not exist: {folder}")
                    continue
                
                logger.info(f"Monitoring folder: {folder}")
                event_handler = FileEventHandler(self)
                self.observer.schedule(event_handler, str(folder), recursive=True)
            
            self.observer.start()
            logger.info("File monitoring started")
    
    def stop(self) -> None:
        """Stop monitoring"""
        with self.lock:
            if self.observer is None:
                logger.warning("File monitor is not running")
                return
            
            self.stopped.set()
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("File monitoring stopped")
    
    def scan_existing_files(self) -> List[str]:
        """
        Scan existing files in watch folders
        
        Returns:
            List of file paths
        """
        all_files = []
        
        for folder in self.watch_folders:
            if not folder.exists():
                logger.warning(f"Watch folder does not exist: {folder}")
                continue
            
            logger.info(f"Scanning folder: {folder}")
            for root, _, files in os.walk(str(folder)):
                for file in files:
                    file_path = os.path.join(root, file)
                    if self._is_valid_file(file_path):
                        all_files.append(file_path)
        
        logger.info(f"Found {len(all_files)} existing files")
        return all_files


class FileEventHandler(FileSystemEventHandler):
    """Handle file system events"""
    
    def __init__(self, file_monitor: FileMonitor):
        """
        Initialize the event handler
        
        Args:
            file_monitor: File monitor instance
        """
        self.file_monitor = file_monitor
        self.debounce_time = 1.0  # seconds
        self.debounce_events = {}
        self.lock = threading.RLock()
    
    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation event"""
        if event.is_directory:
            return
        
        # Handle the event with debouncing
        self._handle_event(event.src_path, 'created')
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification event"""
        if event.is_directory:
            return
        
        # Handle the event with debouncing
        self._handle_event(event.src_path, 'modified')
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion event"""
        if event.is_directory:
            return
        
        # Handle immediately (no debouncing for deletes)
        path = event.src_path
        if self.file_monitor._is_in_watched_folders(path):
            self.file_monitor.on_file_deleted(path)
    
    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move event"""
        if event.is_directory:
            return
        
        # Handle as delete + create
        src_path = event.src_path
        dest_path = event.dest_path
        
        if self.file_monitor._is_in_watched_folders(src_path):
            self.file_monitor.on_file_deleted(src_path)
        
        if self.file_monitor._is_in_watched_folders(dest_path) and self.file_monitor._is_valid_file(dest_path):
            # Handle with debouncing
            self._handle_event(dest_path, 'created')
    
    def _handle_event(self, path: str, event_type: str) -> None:
        """
        Handle an event with debouncing
        
        Args:
            path: File path
            event_type: Event type (created or modified)
        """
        if not self.file_monitor._is_valid_file(path):
            return
        
        with self.lock:
            # Cancel any pending timer for this path
            if path in self.debounce_events:
                self.debounce_events[path].cancel()
            
            # Create a new timer
            timer = threading.Timer(
                self.debounce_time,
                self._process_event,
                args=[path, event_type]
            )
            timer.daemon = True
            self.debounce_events[path] = timer
            timer.start()
    
    def _process_event(self, path: str, event_type: str) -> None:
        """
        Process a debounced event
        
        Args:
            path: File path
            event_type: Event type (created or modified)
        """
        with self.lock:
            if path in self.debounce_events:
                del self.debounce_events[path]
        
        # Avoid processing the same file multiple times simultaneously
        if path in self.file_monitor.processing_files:
            return
        
        self.file_monitor.processing_files.add(path)
        try:
            if event_type == 'created':
                self.file_monitor.on_file_added(path)
            elif event_type == 'modified':
                self.file_monitor.on_file_modified(path)
        finally:
            self.file_monitor.processing_files.remove(path)
