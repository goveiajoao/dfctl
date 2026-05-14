install: ./src/main.go
	go build -C ./src -o /usr/local/bin/dfctl
uninstall:
	rm -f /usr/local/bin/dfctl
