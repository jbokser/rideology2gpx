VERSION := $(shell ./rideology2gpx --version)

default:
	@echo "DISCLAIMER: This tool is for developer use only. Don't use it if you don't know exactly what you're doing."
	@echo "\nUsage:\n"
	@echo "   make version\n      shows the version (v$(VERSION)).\n"
	@echo "   make tag\n      creates a repo tag named as v$(VERSION) for the last commit.\n"
	@echo "   make build\n      creates the packages for distribution.\n"
	@echo "   make upload\n      uploads the packages for distribution to PyPI.\n"
	@echo "   make dist\n      creates the packages for distribution and uploads to PyPI.\n"
	@echo "   make clean\n      does some cleanup on the repository.\n"
	@echo "   make delete_local_tag\n      deletes the local repo tag named as v$(VERSION).\n"
	@echo "   make delete_remote_tag\n      deletes the remote repo tag named as v$(VERSION).\n"

version:
	@echo "v$(VERSION)"

tag:
	git tag -a "v$(VERSION)" -m "v$(VERSION)"

build:
	rm -rf dist
	python3 setup.py sdist

upload:
	twine upload dist/*

dist: build upload

clean:
	rm -rf rideology2gpx.egg-info
	rm -rf __pycache__
	rm -rf */__pycache__
	rm -rf */*/__pycache__
	rm -rf dist
	rm -rf build

delete_local_tag:
	git tag -d "v$(VERSION)"

delete_remote_tag:
	git push --delete origin "v$(VERSION)"
