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
restart_policy_key = 'restart_policy'

# If you want to use this script for yourself but you're not using all of these products,
# remove the products you aren't using from this list.
product_names = [hub_key, youtrack_key, upsource_key, teamcity_key]


def ensure_config_valid(conf: configparser.ConfigParser):
    print("Validating config. THIS ONLY CHECKS FOR THINGS THAT ARE BLANK. YOU SHOULD CHECK YOUR CONFIG YOURSELF")
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
            assert conf[section][restart_policy_key]
            # TeamCity only has a data directory and a logs directory
            if section != teamcity_key:
                assert conf[section][conf_dir_key]
                assert conf[section][backups_dir_key]


def exec_ssh_print(ssh_client: paramiko.SSHClient, command: str):
    std_in, std_out, std_err = ssh_client.exec_command(command)
    for line_out in std_out.read().splitlines():
        print(line_out.decode("utf-8"))


def container_state_status(ssh_client: paramiko.SSHClient, container_id: str, sudo_pwd: str):
    std_out, std_err = exec_ssh(ssh_client,
                                f"echo {sudo_pwd} | "
                                r"sudo -S -k docker container inspect -f '{{.State.Status}}' "
                                f"{container_id}")
    return std_out.rstrip()


def exec_ssh(ssh_client: paramiko.SSHClient, command: str):
    std_in, std_out, std_err = ssh_client.exec_command(command)
    std_out_str = std_out.read().decode("utf-8")
    std_err_str = std_err.read().decode("utf-8")
    if len(std_err_str) > 0:
        # "[sudo] password for YOUR_USERNAME: " is expected when running commands by piping the password to sudo
        if not std_err_str.startswith('[sudo] password for ') and not std_err_str.endswith(': '):
            raise Exception(f'The command "{command}" unexpectedly resulted in output to stderr:\n'
                            f'{std_err_str}')
    return std_out_str, std_err_str


def build_docker_run_cmd(conf: configparser.ConfigParser, product_name: str, ):
    run_cmd = f'docker run -d --restart {config[product_name][restart_policy_key]} --name {config[product_name][name_key]} '
    # Because TeamCity is so rebellious, it uses a data dir with a different name. Almost forgot about that
    run_cmd += f'-v {conf[product_name][data_dir_key]}:' \
               f'{"/data/teamcity_server/datadir" if product_name == teamcity_key else f"/opt/{product_name}/data"} '
    run_cmd += f'-v {conf[product_name][logs_dir_key]}:/opt/{product_name}/logs '
    # TeamCity only has a data directory and a logs directory
    if product_name != teamcity_key:
        run_cmd += f'-v {conf[product_name][conf_dir_key]}:/opt/{product_name}/conf '
        run_cmd += f'-v {conf[product_name][backups_dir_key]}:/opt/{product_name}/backups '
    # The port used inside the docker container for TeamCity is 8111, all other product_names use 8080
    run_cmd += f'-p {conf[product_name][port_key]}:{8111 if product_name == teamcity_key else 8080} '
    # TeamCity image name is teamcity-server, all other product_names use just their name (all lowercase)
    run_cmd += f'jetbrains/{teamcity_key + "-server" if product_name == teamcity_key else product_name}' \
               f':{conf[product_name][version_key]} '
    return run_cmd


def wait_until_stopped(ssh_client: paramiko.SSHClient, container_id: str, sudo_pwd: str):
    status = container_state_status(ssh_client, container_id, sudo_pwd)
    print(f'Waiting for container "{container_id}" to stop.')
    print(f'Current status: {status}')
    while status == 'running':
        print('Sleeping 5 seconds before checking again.')
        exec_ssh_print(ssh, f'sleep 10')
        status = container_state_status(ssh_client, container_id, sudo_pwd)
        print(f'Current status: {status}')
    print(f'Container "{container_id}" is no longer running. Proceeding.')


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
# Prevents the password leaking into the history since it's included in the next command
ssh.exec_command("export HISTIGNORE='*sudo -S*'")
print('Listing running docker containers')
exec_ssh_print(ssh, f'echo {password} | sudo -S -k docker ps -a')
print('\n\n')
for product in product_names:
    print(f'Temporarily disabling restart policy on {config[product][name_key]}')
    exec_ssh(ssh, f'echo {password} | sudo -S -k docker update --restart=no {config[product][name_key]}')
    print(f'Stopping {config[product][name_key]}')
    # Running the "stop" command bundled with JetBrains Docker containers gracefully shuts down the container.
    # See https://www.jetbrains.com/help/hub/start-stop-hub-docker.html#stop-docker-container
    exec_ssh(ssh, f'echo {password} | sudo -S -k docker exec {config[product][name_key]} stop')
    wait_until_stopped(ssh_client=ssh, container_id=config[product][name_key], sudo_pwd=password)
    print(f'Removing {config[product][name_key]}')
    exec_ssh(ssh, f'echo {password} | sudo -S -k docker rm {config[product][name_key]}')
    print(f'Running {config[product][name_key]}')
    exec_ssh(ssh, f'echo {password} | sudo -S -k {build_docker_run_cmd(config, product_name=product)}')
    print('\n\n')
print('Sleeping for 10 seconds')
exec_ssh(ssh, f'sleep 10')
print('Listing running docker containers')
exec_ssh_print(ssh, f'echo {password} | sudo -S -k docker ps -a')

ssh.close()
