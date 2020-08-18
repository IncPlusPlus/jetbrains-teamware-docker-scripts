# JetBrains Team Tools Docker Scripts
This is repository contains scripts that help maintain Docker instances of team tools created by JetBrains. These tools are [Hub](https://www.jetbrains.com/hub/), [TeamCity](https://www.jetbrains.com/teamcity/), [Upsource](https://www.jetbrains.com/upsource/), and [YouTrack](https://www.jetbrains.com/youtrack/).

At the moment, there is only one Python script and one shell script. The shell script will soon be converted to Python.

## Supported Tools
| Tool     | Supported          | Product page                                                                        | Docker image                                                                                        |
|----------|--------------------|-------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| Hub      | :heavy_check_mark: | [<img src="images/hub.svg" width="50" height="50"/>](https://www.jetbrains.com/hub/)           | [<img src="images/the_cube.png" width="50" height="50"/>](https://hub.docker.com/r/jetbrains/hub)              |
| TeamCity | :heavy_check_mark: | [<img src="images/teamcity.svg" width="50" height="50"/>](https://www.jetbrains.com/teamcity/) | [<img src="images/the_cube.png" width="50" height="50"/>](https://hub.docker.com/r/jetbrains/teamcity-server/) |
| Upsource | :heavy_check_mark: | [<img src="images/upsource.svg" width="50" height="50"/>](https://www.jetbrains.com/upsource/) | [<img src="images/the_cube.png" width="50" height="50"/>](https://hub.docker.com/r/jetbrains/upsource/)        |
| YouTrack | :heavy_check_mark: | [<img src="images/youtrack.svg" width="50" height="50"/>](https://www.jetbrains.com/youtrack/) | [<img src="images/the_cube.png" width="50" height="50"/>](https://hub.docker.com/r/jetbrains/youtrack/)        |
| Datalore | :x:                | [<img src="images/datalore.svg" width="50" height="50"/>](https://datalore.jetbrains.com/)     | N/A                                                                                                 |
| Space    | :x:                | [<img src="images/space.svg" width="50" height="50"/>](https://www.jetbrains.com/space/)       | N/A                                                                                                 |

## Contents
Below is an explanation of what each script does and how to use them.

### [Recreate all containers](Recreate all containers.py)
This script will shut down, remove, and recreate all of your teamware containers according to the specifications you outlined in your config file (see the Usage section below).

There are a few use cases for this script. I primarily use it to update the image that my containers run. You may also be able to revive a bugged-out container if something went haywire (although the issue may persist if it is caused by any configuration as the most configuration is persisted _outside_ the container).

#### Usage
Create a copy of [config_example.ini](config_example.ini) and name it `config.ini`. You should keep this copy in the same directory as the example config. If you are not using one or more of the JetBrains products, you can simply remove them from the `product_names` list.

#### Configuring `config.ini`
Most of the config has been completed for you. However, there are a few things you _must_ do before running the script. This may look intimidating but this only needs to be done _once_ and then it's smooth sailing.
- For whatever directories you have set for `data_dir`, `conf_dir`, `logs_dir`, and `backups_dir`, **_be absolutely sure_** that you have followed the instructions for that specific product. For example, Hub needs its folders to be created with file mode `750` as well as be owned by user `13001` and group `13001`.
  - You can find the instructions for creating the folders and setting permissions on the Docker image's page on DockerHub. Links are available in [the table above](#user-content-supported-tools). **DO NOT APPLY THE INSTRUCTIONS FOR ONE PRODUCT TO ANOTHER** there are differences between some of the images and you _will_ run into issues if you ignore them.
  - You may use the directories they are currently set to. These are already reasonable names and you don't have to change them. Just be sure these directories actually exist and the permissions have been set correctly. Note that TeamCity only has a `data_dir` and a `logs_dir` because it just _has_ to be different... :confused:
- This script expects you to have added yourself to the `.ssh/authorized_keys` on the remote server
  - To do this, you must run `ssh-copy-id [username@hostname]` on your computer where `hostname` is either the hostname or IP address of the server you intend to run these containers on and `username` is a super user on that server.
  - If you get the message `/usr/bin/ssh-copy-id: ERROR: No identities found`, you must first run `ssh-keygen` which will guide you through creating a public and private SSH key. Then, try again.
- `key_filename` must be set to the full path of `id_rsa.pub`.
  - The default location for this is `/home/your_username/.ssh/id_rsa.pub` on *nix and `C:\Users\your user name\.ssh\id_rsa.pub` on Windows. You're usually told the location if you've just run `ssh-keygen` with a message like `Your public key has been saved in /home/ryan/.ssh/id_rsa.pub`.
- `username` and `hostname` in `config.ini` _must_ be set to the same values that you used when you ran `ssh-copy-id`.

Breathe out. You're done with the initial steps. Most of the `config.ini` options are peppered with comments explaining what they are for. You should be set from here.

#### Running
Go ahead and run the script. It will ask for your password and then it will tear down and rebuild all of your containers.