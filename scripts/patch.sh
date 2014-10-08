#!/bin/bash
#
# filename: patch.sh
# Author  : Scemoon
# Mail    : mengsan8325150@gmail.com

# Descriptions:
#   If you want to test the linux or unix system with unixbench tool,
# and you want to test multi parallel, then you may be occor error.
# When I develop the lpt suite, I run shell scripts using the api of 
# subprocess, but the subprocess module had a bug what pipe may be
# broken in multi parallel.So if you want using unixbench tool, you 
# need to fix this bug. patch.sh can fix

#set -x

ABSPATH=`echo $0|grep "^/"` 
if test "x$ABSPATH" = "x";then
     SCRIPTS_DIR=`dirname $PWD/$0` 
     #SCRIPTS_DIR=`dirname $SCRIPTS_DIR`
else
     SCRIPTS_DIR=`dirname $0`
fi
# Get the lpt suite root dir
LPT_DIR=`dirname $SCRIPTS_DIR`
FIX_SED=$SCRIPTS_DIR/fix.sed

function CheckRoot(){ current_user=`whoami`
    if test $current_user != "root"; then
        echo "  Current User is `whoami`, but fix python2.x bug that need the root user, please su root"
	exit
    else
	echo "  Current User is root."
    fi   
}

function CheckBit(){
    BIT=`getconf LONG_BIT`
    if [[ $BIT -eq 64 ]]; then
	echo "  The System is 64 OS"
        SUBPROCESS_PATH=`find /usr/lib64 -path "/usr/lib64/python2.*/subprocess.py" -print`
    else
	echo "  The System is 32 OS"
        SUBPROCESS_PATH=`find /usr/lib -path "/usr/lib/python2.*/subprocess.py" -print`
    fi
}
function CheckFix(){
    SUBPROCESS_PATH=$1
    MATCH=`grep "ignals = ('SIGPIPE', 'SIGXFZ', 'SIGXFSZ')" $SUBPROCESS_PATH`
    if [[ "X"$MATCH == "X" ]] ;then
        return 1
    else
        return 0
    fi
}
function FixBug(){
    SUBPROCESS_PATH=$1
    CheckFix $SUBPROCESS_PATH
    RETURN_VALUE=$?
    if [[ $RETURN_VALUE -eq 0 ]]; then
        echo "Python2.x Bug had fixed"
	exit 0
    else
        echo "Pyhon2.x had Bug, need to fixed"
    fi

    $FIX_SED -i $SUBPROCESS_PATH
    if [[ $? -eq 0 ]];then
        echo "Fix Python2.x Bug PASS"
    else
        echo "Fix Python2.x Bug FAIL"  
    fi
}

echo "@-- Begin fix Python2.x Bug"
echo 
echo "@-- Check if root"
CheckRoot
echo
echo "@-- Check System Bit"
CheckBit
echo
echo "@-- Fix Python2.x Bug"
FixBug $SUBPROCESS_PATH
