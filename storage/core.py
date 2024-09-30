from abc import ABC, abstractmethod
from typing import Optional, Any


class KeyValueStorage(ABC):
    @abstractmethod
    def write(self, table: str, key: str, value: Any) -> None:
        """
        Write a key-value pair. Overwrites any existing value.
        """
        pass

    @abstractmethod
    def read(self, table: str, key: str) -> Optional[Any]:
        """
        Get the value associated with a certain key.
        """
        pass

    @abstractmethod
    def read_all(self, table: str) -> Optional[Any]:
        """
        Get the value associated with a certain key.
        """
        pass

    @abstractmethod
    def delete(self, table: str, key: str) -> None:
        """
        Delete a key-value pair by the key.
        """
        pass

    @abstractmethod
    def clear_table(self, table: str) -> None:
        """
        Clear all key-value pairs from a specific table.
        """
        pass


class InMemoryKeyValueStorage(KeyValueStorage):
    def __init__(self):
        # Dictionary to hold tables, each table is itself a dictionary for key-value pairs
        self.storage = {}

    def write(self, table: str, key: str, value: Any) -> None:
        if table not in self.storage:
            self.storage[table] = {}
        self.storage[table][key] = value

    def read(self, table: str, key: str) -> Optional[Any]:
        return self.storage.get(table, {}).get(key, None)

    def delete(self, table: str, key: str) -> None:
        if table in self.storage and key in self.storage[table]:
            del self.storage[table][key]

    def clear_table(self, table: str) -> None:
        if table in self.storage:
            self.storage[table].clear()

    def read_all(self, table: str) -> Optional[dict]:
        """
        Read all key-value pairs in a specific table.
        """
        return self.storage.get(table, None)

# Example usage:
if __name__ == "__main__":
    kv_store = InMemoryKeyValueStorage()

    # Write to the store
    kv_store.write('polling_results', 'BTCUSDT', {'price': '50000', 'volume': '1000'})
    kv_store.write('polling_results', 'ETHUSDT', {'price': '4000', 'volume': '2000'})

    # Read a value
    print(kv_store.read('polling_results', 'BTCUSDT'))  # Output: {'price': '50000', 'volume': '1000'}

    # Delete a value
    kv_store.delete('polling_results', 'ETHUSDT')
    print(kv_store.read('polling_results', 'ETHUSDT'))  # Output: None

    # Clear a table
    kv_store.clear_table('polling_results')
    print(kv_store.read_all('polling_results'))  # Output: None
