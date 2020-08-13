to build the image : 
``̀ 
docker build . --tag vpnlinux
```
execute a command inside docker (default is bash)

docker run -it --volume $(pwd):/home/user/protonvpn-nm-core  vpnlinux
