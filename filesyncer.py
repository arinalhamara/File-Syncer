import os
import hashlib
import shutil
import argparse
import threading
from queue import Queue

class FileSyncer:
    def __init__(self, source, destination, threads=4):
        self.source = source
        self.destination = destination
        self.threads = threads
        self.queue = Queue()

    def hash_file(self, file_path):
        """Menghasilkan hash SHA-256 untuk file"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(4096):
                hasher.update(chunk)
        return hasher.hexdigest()

    def sync_file(self, src_file, dest_file):
        """Sinkronisasi file jika berbeda"""
        if os.path.exists(dest_file):
            if self.hash_file(src_file) == self.hash_file(dest_file):
                return  # File tidak berubah
        shutil.copy2(src_file, dest_file)
        print(f'Copied: {src_file} -> {dest_file}')

    def worker(self):
        while True:
            item = self.queue.get()
            if item is None:
                break
            src_file, dest_file = item
            self.sync_file(src_file, dest_file)
            self.queue.task_done()

    def sync(self):
        """Menjalankan sinkronisasi file"""
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self.worker)
            t.start()
            threads.append(t)
        
        for root, _, files in os.walk(self.source):
            rel_path = os.path.relpath(root, self.source)
            dest_root = os.path.join(self.destination, rel_path)
            os.makedirs(dest_root, exist_ok=True)
            
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_root, file)
                self.queue.put((src_file, dest_file))
        
        self.queue.join()
        
        for _ in range(self.threads):
            self.queue.put(None)
        for t in threads:
            t.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FileSyncer - Sinkronisasi file dengan hashing dan multithreading.")
    parser.add_argument("source", help="Direktori sumber")
    parser.add_argument("destination", help="Direktori tujuan")
    parser.add_argument("-t", "--threads", type=int, default=4, help="Jumlah thread (default: 4)")
    args = parser.parse_args()
    
    syncer = FileSyncer(args.source, args.destination, args.threads)
    syncer.sync()
