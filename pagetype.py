# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

from enum import Enum

class PageType(Enum):
    ROM = 1
    RAM = 2
    SCC = 3
    DISK = 4
    MEMMAP = 5
