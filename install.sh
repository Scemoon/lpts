#!/bin/bash
#
# Filename: install.sh
# Update Date:  2014/10/
# Author:  Scemoon
# Mail: mengsan8325150@gmail.com

# Descriptions:
# install.sh intend to install lpt suite into OS, We can run lpt
# suite with system init-scripts . When one of tools had 
# run completed , you can choice if reboot system and reboot auto 
# run lpt suite when system start. Another, you can 
# patch the python bug.

#set -x
LOG=/dev/null
#
ABSPATH=`echo $0|grep "^/"`
if test "x$ABSPATH" = "x";then
     LPT_DIR=`dirname $PWD/$0` 
     #LPT_DIR=`dirname $0`
else
     LPT_DIR=`dirname $0`
fi
# Get the lpt suite root dir
SCRIPTS_DIR="$LPT_DIR/scripts"

PATCH_FILE=$SCRIPTS_DIR/patch.sh
FIX_SED=$SCRIPTS_DIR/fix.sed
LPTD_PATH=$SCRIPTS_DIR/lptd


function CheckRoot(){ current_user=`whoami`
    if test $current_user != "root"; then
        echo "  Current User is `whoami`, but fix python2.x bug that need the root user, please su root"
        exit
    else
        echo "  Current User is root."
    fi
}


function Echo(){
    strs=$1
    echo "lpt--`date +%m.%d-%H:%M:%S`--$strs"

}

function init_strings(){
cat<<EOF>/etc/init.d/lptd
#!/bin/sh 
# chkconfig: 2345 99 25 
# description: linux performance test suite

### BEGIN INIT INFO 
# Provides:          lptd 
# Required-Start:    \$remote_fs \$network \$named   
# Required-Stop:     \$remote_fs \$network \$named   
# Default-Start:     2 3 4 5 
# Default-Stop:      0 1 6   
# Short-Description: linux performance test suite 
### END INIT INFO   
exec $LPTD_PATH "\$@" 
EOF
}

function install_server(){
    #link lptd to init.d
    if [ ! -f "/etc/init.d/lptd" ];then
        init_strings
        chmod +x /etc/init.d/lptd >> $LOG
        chkconfig --level 2345 lptd on >> $LOG
        service lptd start >> $LOG
    fi 
}

Echo "Begin install lpt suite"
Echo "Check if root"
    CheckRoot
Echo "Patch Python Bug"
    $PATCH_FILE
   
Echo "Install lptd server"
    install_server

