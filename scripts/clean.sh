#!/bin/bash 
#

ABSPATH=`echo $0|grep "^/"`
if test "x$ABSPATH" = "x";then
    SCRIPTS_DIR=`dirname $PWD/$0`
    SCRIPTS_DIR=`dirname $SCRIPTS_DIR`
else
    SCRIPTS_DIR=`dirname $0`
fi

#if test `basename $SCRIPTS_DIR` = ".";then
#   SCRIPTS_DIR=`dirname $SCRIPTS_DIR`
#fi
LPT_DIR=`dirname $SCRIPTS_DIR`
TMP_DIR=$LPT_DIR/tmp
SRC_DIR=$LPT_DIR/src
BIN_DIR=$LPT_DIR/bin
LOG_DIR=$LPT_DIR/logs


for DIR in $TMP_DIR $SRC_DIR $BIN_DIR;do
    #echo $DIR
    cd $DIR
    rm -rf *
    if [[ $? -eq 0 ]];then
        echo "@* clean $DIR PASS"
    else
        echo "@* clean $DIR FAIL"
    fi
done


#清空日志
cd $LOG_DIR
echo "" >Test.log && echo "clean log PASS"

