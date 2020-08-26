## Manage the Image


### Build the image on your computer

``̀ sh
$ make local
```

This command is going to generate an image: `nm-core:latest`


## Run tests

> No need to build the image first, we build it before we execute the test command

```
$ make test
```

This command is going to execute:

```sh
$ docker run \
    --rm \
    -u user \
    --privileged \
    --volume $(pwd):/home/user/protonvpn-nm-core \
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

### Mode interactive

execute a command inside docker (default is bash)

```sh
$ docker run \
  -u user \
  -it \
  --privileged \
  --volume $(pwd):/home/user/protonvpn-nm-core \
  nm-core:latest
```

You can test the keyring backend in the docker as per : https://unix.stackexchange.com/questions/473528/how-do-you-enable-the-secret-tool-command-backed-by-gnome-keyring-libsecret-an


```sh
secret-tool lookup foo bar
printf "aPassword" | secret-tool store --label="test" foo bar
secret-tool lookup foo bar
```
