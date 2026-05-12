install: main.go
	go install
	go build -o /usr/local/bin/dfctl
uninstall:
	rm -f /usr/local/bin/dfctl
