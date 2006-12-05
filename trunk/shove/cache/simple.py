# Copyright (c) 2005, the Lawrence Journal-World
# Copyright (c) 2006 L. C. Rees
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#    3. Neither the name of Django nor the names of its contributors may be used
#       to endorse or promote products derived from this software without
#       specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''Single-process in-memory cache.

The shove psuedo-URL for a simple cache is:

simple://
'''

import time
import random
from shove.cache import BaseCache

__all__ = ['SimpleCache']


class SimpleCache(BaseCache):

    '''Single-process in-memory cache.'''    
    
    def __init__(self, engine, **kw):
        super(SimpleCache, self).__init__(engine, **kw)
        # Get random seed
        random.seed()
        # Set maximum number of items to cull if over max
        self._maxcull, self._cache = kw.get('maxcull', 10), dict()
        # Set max entries
        self._max_entries = kw.get('max_entries', 300)

    def __getitem__(self, key):
        values = self.loads(self._cache[key]) 
        # Delete if item timed out.
        if values[0] < time.time():
            del self._cache[key]
            raise KeyError('%s' % key)
        return values[1]

    def __setitem__(self, key, value):
        # Cull values if over max # of entries
        if len(self) >= self._max_entries: self._cull()
        self._cache[key] = self.dumps((time.time() + self.timeout, value)) 

    def __delitem__(self, key):
        try:
            del self._cache[key]
        except KeyError:
            raise KeyError('%s' % key)

    def __len__(self):
        return len(self._cache)
        
    def _cull(self):
        '''Remove items in cache to make roomt.'''
        # Cull number of items allowed (set by _maxcull)
        num = 0
        for key in self._cache.keys():
            if num <= self._maxcull:
                # Remove item if expired
                try:
                    self[key]
                except KeyError:
                    num += 1
            else: break
        # Check if sufficient space has been created
        while len(self) >= self._max_entries and num <= self._maxcull:
            # Cull remainder of allowed quota at random
            del self[random.choice(self._cache.keys())]