install: main.go
	go build -o /usr/local/bin/dfctl
uninstall:
	rm -f /usr/local/bin/dfctl
