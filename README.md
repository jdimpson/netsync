Python 3 library to be used to synchronize actions/messaging across an IP network. Initial use case is coordinating RGB lights across multiple processors.

Currently includes a subclass around python's socket class that implements Real Time Protocol, although the implementation is far from finished.

Next step is to implement one or more helper classes to make synchronizing two or more devices operating in lockstep, including measurement of the latency to so that it doesn't matter which system is the lead system (which would otherwise execute every step sooner than the following systems.)
