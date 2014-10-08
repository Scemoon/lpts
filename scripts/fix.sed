#!/bin/sed -f
#
# Description:
# Fix The Subprocess.py BUG.

/os.chdir(cwd)/ a\
                            signals = ('SIGPIPE', 'SIGXFZ', 'SIGXFSZ') \
                            for sig in signals: \
                                if hasattr(signal, sig): \
                                    signal.signal(getattr(signal, sig), signal.SIG_DFL) 
