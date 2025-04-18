# Installs or uninstalls the bot as a Linux systemd service

help:
	@echo This script sets up the audax-tracker Telegram as a systemd service, or removes that service.
	@echo Please make one of the following targets.  Note that you will need superuser privileges.
	@echo - install: install the bot as a systemd service
	@echo - uninstall: uninstall the service but keep configuration and data
	@echo - purge: uninstall the service and delete configuration and data

.PHONY: all bot install uninstall

.FORCE:

unit_name=audax-tracker
lib_dir=/usr/local/lib/${unit_name}
conf_dir=/usr/local/etc/${unit_name}
service_dir=/etc/systemd/system
data_dir=/var/local/${unit_name}
venv=${lib_dir}/venv

install: $(service_dir) audax-tracker.service
	@echo Installing the service files...
	cp audax-tracker.service $(service_dir)
	chown root:root $(service_dir)/audax-tracker.service
	chmod 644 $(service_dir)/audax-tracker.service

	@echo Installing library files...
	mkdir -p $(lib_dir)
	cp src/bot.py $(lib_dir)/bot.py
	mkdir -p $(lib_dir)/common
	cp src/common/__init__.py $(lib_dir)/common/__init__.py
	cp src/common/defaults.py $(lib_dir)/common/defaults.py
	cp src/common/i18n.py $(lib_dir)/common/i18n.py
	cp src/common/log.py $(lib_dir)/common/log.py
	cp src/common/settings.py $(lib_dir)/common/settings.py
	cp src/common/state.py $(lib_dir)/common/state.py
	mkdir -p $(lib_dir)/locales/en/LC_MESSAGES
	cp src/locales/en/LC_MESSAGES/bot.mo $(lib_dir)/locales/en/LC_MESSAGES/bot.mo
	mkdir -p $(lib_dir)/locales/ru/LC_MESSAGES
	cp src/locales/ru/LC_MESSAGES/bot.mo $(lib_dir)/locales/ru/LC_MESSAGES/bot.mo

	chown root:root $(lib_dir)/*
	chmod 644 $(lib_dir)

	@echo Installing configuration files...
	mkdir -p $(conf_dir)
	cp audax-tracker.env $(conf_dir)
	cp src/settings.yaml $(conf_dir)
	chown root:root $(conf_dir)/*
	chmod 644 $(conf_dir)

	@echo Preparing persistent storage...
	mkdir -p $(data_dir)

	@echo Creating virtual environment for Python 3.11 and installing packages...
	python3.11 -m venv $(venv)
	$(venv)/bin/pip3 install -r requirements.txt

	@echo Installation complete...
	@echo run 'systemctl start audax-tracker' to start the service
	@echo run 'systemctl status audax-tracker' to view status
	@echo run 'systemctl stop audax-tracker' to stop the service

uninstall:
	@echo Stopping and disabling the service...
	-systemctl stop audax-tracker
	-systemctl disable audax-tracker
	@echo Deleting library files...
	-rm -r $(lib_dir)
	@echo Deleting service files...
	-rm -r $(service_dir)/audax-tracker.service
	@echo Uninstallation complete.

purge: uninstall
	@echo Deleting persistent data...
	-rm -r $(data_dir)
	@echo Deleting configuration files...
	-rm -r $(conf_dir)
	@echo Purge complete.
