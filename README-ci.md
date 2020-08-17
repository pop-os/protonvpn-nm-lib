to build the image : 

``̀ 
docker build . --tag vpnlinux
```

execute a command inside docker (default is bash)

```
docker run -u user -it --privileged --volume $(pwd):/home/user/protonvpn-nm-core  vpnlinux
```

You can test the keyring backend in the docker as per : https://unix.stackexchange.com/questions/473528/how-do-you-enable-the-secret-tool-command-backed-by-gnome-keyring-libsecret-an


```
secret-tool lookup foo bar
printf "aPassword" | secret-tool store --label="test" foo bar
secret-tool lookup foo bar
```
