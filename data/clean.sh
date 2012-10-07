#!/bin/bash

# CLEANUP SAVED MEDIA.


# for date-criteria use find e.g.:
# FILES = find . -type d -mtime +10 | egrep '[0-9a-f]{32}'
FILES=`ls | egrep '[0-9a-f]{32}'`
[ -z "$FILES" ] || echo rm -rf $FILES

