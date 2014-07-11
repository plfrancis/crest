. /etc/clearwater/config
hs_prov_port=`echo $hs_provisioning_hostname | perl -p -e 's/.+:(\d+)/$1/'`
cat << EOF
# A simple configuration file for monitoring the local host
# This can serve as an example for configuring other servers;
# Custom services specific to this host are added here, but services
# defined in icinga-common_services.cfg may also apply.
#

define command{
        command_name    restart-hs-prov
        command_line    /usr/lib/nagios/plugins/clearwater-abort \$SERVICESTATE$ \$SERVICESTATETYPE$ \$SERVICEATTEMPT$ /var/run/homestead_prov.pid 30
        }


define service{
        use                             cw-service         ; Name of service template to use
        host_name                       local_ip
        service_description             Homestead-prov port open
	check_command                   http_ping!$hs_prov
        event_handler                   restart-hs-prov
        }

EOF
