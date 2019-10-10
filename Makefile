.PHONY: test

venv:
	# Need to install pip separately into the venv for Debian/Ubuntu systems
	test -d venv || { python3 -m venv venv --without-pip && . venv/bin/activate; \
		wget https://bootstrap.pypa.io/get-pip.py -O venv/bin/get-pip.py && \
		chmod u+x venv/bin/get-pip.py && venv/bin/get-pip.py; }
	ls .activate.sh > /dev/null || ln -s venv/bin/activate .activate.sh
	echo "deactivate" > .deactivate.sh

install: venv
	. venv/bin/activate; pip install .

test: install requirements-dev.txt
	. venv/bin/activate; pip install -r requirements-dev.txt && coverage run -m pytest -v

clean:
	rm -rf venv pygmy.egg-info build dist .coverage .pytest_cache .activate.sh
	find . -iname "*.pyc" -delete
