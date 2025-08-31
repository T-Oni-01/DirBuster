import argparse
import requests
import threading
import queue
import time
import sys
from urllib.parse import urljoin, urlparse


class DirBuster:
    def __init__(self, target_url, wordlist_file, threads=10, timeout=5):
        self.target_url = target_url.rstrip('/')
        self.wordlist_file = wordlist_file
        self.threads = threads
        self.timeout = timeout
        self.queue = queue.Queue()
        self.found_paths = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def load_wordlist(self):
        """Load the wordlist from file"""
        try:
            with open(self.wordlist_file, 'r') as f:
                words = [line.strip() for line in f if line.strip()]
            return words
        except FileNotFoundError:
            print(f"Error: Wordlist file '{self.wordlist_file}' not found.")
            sys.exit(1)

    def check_url(self, url):
        """Check if a URL exists"""
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=False)
            if response.status_code < 400:
                return response.status_code
        except requests.RequestException:
            pass
        return None

    def worker(self):
        """Worker thread function"""
        while True:
            try:
                path = self.queue.get(timeout=1)
                url = urljoin(self.target_url, path)

                status_code = self.check_url(url)
                if status_code:
                    self.found_paths.append((path, status_code))
                    print(f"[{status_code}] {url}")

                self.queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                print(f"Error processing {path}: {e}")
                self.queue.task_done()

    def run(self):
        """Run the directory busting process"""
        print(f"Starting DirBuster against: {self.target_url}")
        print(f"Using wordlist: {self.wordlist_file}")
        print(f"Threads: {self.threads}")
        print("-" * 50)


        words = self.load_wordlist()# Load wordlist
        print(f"Loaded {len(words)} words from wordlist")


        for word in words: # Add words to queue
            self.queue.put(word)


        thread_pool = []# Create and start threads
        for _ in range(self.threads):
            thread = threading.Thread(target=self.worker)
            thread.daemon = True
            thread.start()
            thread_pool.append(thread)


        try:# Wait for queue to be processed
            self.queue.join()
        except KeyboardInterrupt:
            print("\n[!] Keyboard interrupt received, shutting down...")

        # Print summary
        print("\n" + "-" * 50)
        print(f"Scan completed. Found {len(self.found_paths)} paths.")

        if self.found_paths:
            print("\nFound paths:")
            for path, status_code in self.found_paths:
                print(f"[{status_code}] {path}")


def main():
    parser = argparse.ArgumentParser(description='A simple DirBuster-like tool')
    parser.add_argument('url', nargs='?', help='Target URL (e.g., http://example.com)')
    parser.add_argument('-w', '--wordlist', default='common.txt',
                        help='Path to wordlist file (default: common.txt)')
    parser.add_argument('-t', '--threads', type=int, default=10,
                        help='Number of threads (default: 10)')
    parser.add_argument('--timeout', type=int, default=5,
                        help='Request timeout in seconds (default: 5)')

    args = parser.parse_args()


    if not args.url: # If URL is not provided as a command-line argument, prompt the user
        print("Welcome to Tai's DirBuster!")
        print("Please enter the target URL to scan.")
        args.url = input("Target URL (e.g., http://example.com): ").strip()
        print()  # Add a blank line for better readability


    if not args.url.startswith(('http://', 'https://')):# Validate URL
        print("Error: URL must start with http:// or https://")
        sys.exit(1)

    # Create and run DirBuster
    dirbuster = DirBuster(args.url, args.wordlist, args.threads, args.timeout)
    dirbuster.run()


if __name__ == '__main__':
    main()