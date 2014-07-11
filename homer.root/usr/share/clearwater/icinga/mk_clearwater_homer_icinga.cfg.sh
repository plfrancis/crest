. /etc/clearwater/config
homer_port=`echo $xdms_hostname | perl -p -e 's/.+:(\d+)/$1/'`
cat << EOF
# A simple configuration file for monitoring the local host
# This can serve as an example for configuring other servers;
# Custom services specific to this host are added here, but services
# defined in icinga-common_services.cfg may also apply.
#

define command{
        command_name    restart-homer
        command_line    /usr/lib/nagios/plugins/clearwater-abort \$SERVICESTATE$ \$SERVICESTATETYPE$ \$SERVICEATTEMPT$ /var/run/homer.pid 30
        }


define service{
        use                             cw-service         ; Name of service template to use
        host_name                       local_ip
        service_description             homer port open
	check_command                   http_ping!$homer_port
        event_handler                   restart-homer
        }

EOF
