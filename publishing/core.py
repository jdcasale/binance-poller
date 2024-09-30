import json
from datetime import datetime

import asyncio
import os

from abc import ABC, abstractmethod
from typing import TextIO

from publishing.parsing import parse_symbols_info
from storage.core import KeyValueStorage
from utils.logging import setup_logging

"""
NB: There is a time limit on this assignment, so the publisher abstraction currently serves as both publisher
 and subscriber/writer for brevity. It's a little half-baked, but exists to make it easy to separate
 the logic of persisting messages from the poller, and it does that well enough.
"""

class Publisher(ABC):
    @abstractmethod
    def publish(self, topic: str, message: dict) -> None:
        """
        Publish a message to a specific topic.
        """
        pass

    def close(self) -> None:
        """
        Close any resources associated with the publisher
        """
        pass

class KeyValueStorePubSub(Publisher):
    def __init__(self, key_value_store: KeyValueStorage) -> None:
        """
        Initializes a publisher/subscriber that updates the server's storage of key-value pairs

        """
        self.key_value_store = key_value_store

    def publish(self, topic: str, message: dict) -> None:
        """
        Write to the underlying store
        """
        if topic == 'exchange_info':
            symbols_info = parse_symbols_info(message)
            for key, value in symbols_info.items():
                self.key_value_store.write('symbols', key, value)
            self.key_value_store.write(topic, 'rateLimits', message['rateLimits'])
        if topic in ['system_status', 'account_info']:
            for key, value in message.items():
                self.key_value_store.write(topic, key, value)

    def close(self) -> None:
        pass


class FilePubSub(Publisher):
    def __init__(self, base_dir: str = 'output', flush_interval: float = 1, flush_limit: int = 10_000) -> None:
        """
        Initializes a publisher/subscriber that periodically flushes writes for each topic to a file.
        Used to maintain a complete historical record of updates.

        Args:
        - base_dir (str): Directory where topic files will be stored
        - flush_interval (float): Time interval (seconds) between async flushes
        - flush_limit (int): Max number of messages to buffer before triggering a synchronous flush
        """
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

        self.file_handles: dict[str, TextIO] = {}
        self.write_counts: dict[str, int] = {}

        self.flush_interval = flush_interval
        self.flush_limit = flush_limit

        self.flush_task = asyncio.create_task(self.flush_periodically())
        self.logger = setup_logging(__name__)

    def _get_file_handle(self, topic: str) -> TextIO:
        """
        Get or create a file handle for the specified topic.
        """
        if topic not in self.file_handles:
            file_path = os.path.join(self.base_dir, f"{topic}.log")
            self.file_handles[topic] = open(file_path, 'a')
            self.write_counts[topic] = 0
        return self.file_handles[topic]

    def publish(self, topic: str, message: dict) -> None:
        """
        Buffer a message to the requested topic.
        Triggers a flush if the total number of buffered writes is too large
        """
        self.logger.info(f'publishing to topic {topic}')
        file_handle = self._get_file_handle(topic)
        message_s = json.dumps(message)
        formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_handle.write(f"{formatted_time} - {message_s}\n")
        self.write_counts[topic] += 1

        # Flush if message count exceeds the limit
        if self.write_counts[topic] >= self.flush_limit:
            self.flush(topic)

    def flush(self, topic: str) -> None:
        """
        Flush the file for the specified topic.
        """
        if topic in self.file_handles:
            self.file_handles[topic].flush()
            self.write_counts[topic] = 0

    async def flush_periodically(self) -> None:
        """
        Periodically flush all open file handles asynchronously.
        """
        while True:
            await asyncio.sleep(self.flush_interval)
            self.flush_all()

    def flush_all(self) -> None:
        """
        Flush all open file handles.
        """
        for topic, file_handle in self.file_handles.items():
            file_handle.flush()
            self.write_counts[topic] = 0

    async def close(self) -> None:
        """
        Close all open file handles and stop the periodic flushing.
        """
        self.flush_task.cancel()
        await asyncio.gather(self.flush_task, return_exceptions=True)
        for file_handle in self.file_handles.values():
            file_handle.close()
        self.file_handles.clear()
        self.write_counts.clear()


class InMemoryWithLogPublisher(Publisher):
    def __init__(self, in_memory: KeyValueStorePubSub, file_backed: FilePubSub):
        self.in_memory = in_memory
        self.file_backed = file_backed

    def publish(self, topic: str, message: dict) -> None:
        """
        Write to the underlying in-memory store
        """
        # In real life we'd want some sort of guarantees around atomicity for these two
        self.file_backed.publish(topic, message)
        self.in_memory.publish(topic, message)

    def close(self) -> None:
        self.in_memory.close()
        self.file_backed.close()