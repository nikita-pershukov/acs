# ACS (access control system)

This is bash and python scripts to have simple and comfort access control system on raspberry pi clients and linux server

## Installing on server from server-script directory

Install and config mail client and mutt to have e-mail notifications about errors

```
aptitude install exim4 mutt
dpkg-reconfigure exim4-config
```

Download acs script

```
git clone https://github.com/nikita-pershukov/acs.git
```

Add user and group for using acs

```
adduser acs
addgroup acs-adm
usermod -a -G acs-adm acs
```

Add symlink to comfort use acs

```
ln -s ./watchdog /usr/local/bin/acs
```

Create "config" file for yourself with same stuff

```
local_login         local_login
local_dir           local_dir_path
logs_dir            logs_dir_path
wait_file           wait_file_name_in_local_dir
```

Add record in crontab (from user acs) to use acs

```
crontab -l > /tmp/mycron
echo "  * *  *   *   *     /usr/local/bin/acs auto" >> /tmp/mycron
crontab /tmp/mycron
rm /tmp/mycron
```
## Installing on client from client-script directory

Download acs script

```
git clone https://github.com/nikita-pershukov/acs.git
```

Add user and group for using acs

```
adduser acs
addgroup acs-adm
usermod -a -G acs-adm acs
```

Add symlink to comfort use acs

```
ln -s ./watchdog /usr/local/bin/acs
```

Create "config" file for yourself with same stuff

```
device_name         device_hostname
srv_ip              local_server_ip
srv_port            local_server_ssh_port
srv_key             rsa_key_2_server_ssh
srv_login           srv_login_2_acs_system
local_login         local_login_2_acs_system
srv_dir             path_2_dir_on_srv_with_client_script
local_dir           local_dir_path
srv_logs_dir        server_logs_dir_path
local_logs_dir      local_logs_dir_path
srv_clients_ip_dir  server_dir_path_2_clients_ip
srv_command         command_filename
srv_web_addr        server_web_url
srv_web_port        server_web_port
acs_config          config_filename
acs_masters         masters_filename
wait_file           wait_file_filename
force_file          force_file_filename
python_script       python_script_filename
python_state        python_script_state
python_token        current_client_python_token
python_salt         current_client_python_salt
python_pin_led_r    pin_on_gpio
python_pin_led_g    pin_on_gpio
python_pin_led_b    pin_on_gpio
python_blinks_good  pin_on_gpio
python_blinks_bad   pin_on_gpio
python_blinks_butt  pin_on_gpio
python_pin_lock     pin_on_gpio
python_pin_butt     pin_on_gpio
python_unlock_time  pin_on_gpio
```

Add record in crontab (from user acs) to use acs

```
crontab -l > /tmp/mycron
echo "  * *  *   *   *     /usr/local/bin/acs auto" >> /tmp/mycron
crontab /tmp/mycron
rm /tmp/mycron
```

## Version

alpha

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE.txt) file for details
