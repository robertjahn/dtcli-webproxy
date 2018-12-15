docker build -t dtcli-webproxy .
docker stop dtcli-webproxy
docker run --rm -p 5000:5000 --name dtcli-webproxy dtcli-webproxy
docker stop dtcli-webproxy