import paramiko
import configparser
import getpass

server_key = 'server'
hub_key = 'hub'
youtrack_key = 'youtrack'
upsource_key = 'upsource'
teamcity_key = 'teamcity'
hostname_key = 'hostname'
username_key = 'username'
key_filename_key = 'key_filename'
data_dir_key = 'data_dir'
conf_dir_key = 'conf_dir'
logs_dir_key = 'logs_dir'
backups_dir_key = 'backups_dir'
name_key = 'name'
port_key = 'port'
version_key = 'version'
# If you want to use this for yourself and you're not using all of these products, just remove some from this check
product_names = [hub_key, youtrack_key, upsource_key, teamcity_key]


def ensure_config_valid(conf: configparser.ConfigParser):
    print("Validating config. THIS ONLY CHECKS FOR THINGS THAT ARE BLANK. CHECK YOUR CONFIG YOURSELF")
    if [server_key] + product_names != conf.sections():
        raise ValueError(
            "Your config.ini has some unknown or missing sections. Check config_example.ini for an example "
            "of what it should look like.")
    for section in conf.sections():
        if section == server_key:
            assert conf[server_key][hostname_key]
            assert conf[server_key][username_key]
            assert conf[server_key][key_filename_key]
        else:
            assert conf[section][name_key]
            assert conf[section][data_dir_key]
            assert conf[section][logs_dir_key]
            assert conf[section][port_key]
            assert conf[section][version_key]
            # TeamCity only has a data directory and a logs directory
            if section != teamcity_key:
                assert conf[section][conf_dir_key]
                assert conf[section][backups_dir_key]


def exec_ssh(ssh_client: paramiko.SSHClient, command: str):
    std_in, std_out, std_err = ssh_client.exec_command(command)
    for line_out in std_out.read().splitlines():
        print(line_out.decode("utf-8"))


def build_docker_run_cmd(conf: configparser.ConfigParser, product_name, ):
    run_cmd = f'docker run -d --restart always --name {config[product][name_key]} '
    run_cmd += f'-v {conf[product][data_dir_key]}:' \
               f'{"/data/teamcity_server/datadir" if product == teamcity_key else f"/opt/{product}/data"} '
    run_cmd += f'-v {conf[product][logs_dir_key]}:/opt/{product}/logs '
    # TeamCity only has a data directory and a logs directory
    if product != teamcity_key:
        run_cmd += f'-v {conf[product][conf_dir_key]}:/opt/{product}/conf '
        run_cmd += f'-v {conf[product][backups_dir_key]}:/opt/{product}/backups '
    # The port used inside the docker container for TeamCity is 8111, all other products use 8080
    run_cmd += f'-p {conf[product][port_key]}:{8111 if product == teamcity_key else 8080} '
    # TeamCity image name is teamcity-server, all other products use just their name (all lowercase)
    run_cmd += f'jetbrains/{teamcity_key + "-server" if product == teamcity_key else product}' \
               f':{conf[product][version_key]} '
    return run_cmd


config = configparser.ConfigParser()
config.read('config.ini')
ensure_config_valid(config)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print(f'Connecting to "{config[server_key][hostname_key]}" with username "{config[server_key][username_key]}" using '
      f'file "{config[server_key][key_filename_key]}"')
ssh.connect(hostname=config[server_key][hostname_key], username=config[server_key][username_key],
            key_filename=config[server_key][key_filename_key])
print("Preparing password prompt. If you aren't prompted for your password, try running this script in some other"
      "form of shell or TTY. The prompt won't appear in PyCharm's runner but will in the debugger.")
password = getpass.getpass('Sudo password: ')
print('\n')  # Make some room
ssh.exec_command("export HISTIGNORE='*sudo -S*'")
print('Listing running docker containers')
exec_ssh(ssh, f'echo {password} | sudo -S -k docker ps -a')
for product in product_names:
    print(f'Stopping {config[product][name_key]}')
    exec_ssh(ssh, f'echo {password} | sudo -S -k docker stop {config[product][name_key]}')
    print(f'Removing {config[product][name_key]}')
    exec_ssh(ssh, f'echo {password} | sudo -S -k docker rm {config[product][name_key]}')
    print(f'Running {config[product][name_key]}')
    exec_ssh(ssh, f'echo {password} | sudo -S -k {build_docker_run_cmd(config, product)}')
print('Sleeping for 10 seconds')
exec_ssh(ssh, f'echo {password} | sudo -S -k sleep 10')
print('Listing running docker containers')
exec_ssh(ssh, f'echo {password} | sudo -S -k docker ps -a')

ssh.close()
