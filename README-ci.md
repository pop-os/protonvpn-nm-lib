## Manage the Image


### Build the image on your computer

```sh
$ make local
```

This command is going to generate an image: `nm-core:latest`


## Run tests

> No need to build the image first, we build it before we execute the test command

```sh
$ make test
```

This command is going to execute:

```sh
$ docker run \
    --rm \
    --privileged \
    --volume $(pwd)/.env:/home/user/protonvpn-nm-core/.env \
    nm-core:latest \
    python3 -m pytest

```
#### About tests

You will need a `.env` file with some keys inside in order to run the tests:

```
vpntest_user
vpntest_pwd
openvpntest_user
openvpntest_pwd
```

### Execute a command from the container

Ex: ls -l

```sh
$ docker run \
  -u user \
  -it \
  --privileged \
  --volume $(pwd):/home/user/protonvpn-nm-core \
  nm-core:latest \
  ls -l
```

Output:
```
total 56
-rw-rw-r-- 1 user user 1039 Aug 21 09:15 Dockerfile
-rw-rw-r-- 1 user user 1310 Aug 26 07:54 Makefile
-rw-rw-r-- 1 user user  113 Aug 20 12:15 Pipfile
-rw-rw-r-- 1 user user 1143 Aug 26 08:00 README-ci.md
-rw-rw-r-- 1 user user  804 Aug 20 12:15 README.md
-rw-rw-r-- 1 user user 7056 Aug 20 12:15 cli.py
-rw-rw-r-- 1 user user 2954 Aug 20 12:15 cli_dialog.py
-rwxrwxr-x 1 user user  777 Aug 26 08:01 docker_entry.sh
drwxrwxr-x 5 user user 4096 Aug 20 12:33 lib
-rw-rw-r-- 1 user user  202 Aug 20 12:15 requirements.txt
-rw-rw-r-- 1 user user   34 Aug 20 12:15 setup.cfg
-rw-rw-r-- 1 user user 1039 Aug 20 12:15 setup.py
drwxrwxr-x 4 user user 4096 Aug 26 07:54 tests
```

You can test the keyring backend in the docker as per : https://unix.stackexchange.com/questions/473528/how-do-you-enable-the-secret-tool-command-backed-by-gnome-keyring-libsecret-an


```sh
secret-tool lookup foo bar
printf "aPassword" | secret-tool store --label="test" foo bar
secret-tool lookup foo bar
```
