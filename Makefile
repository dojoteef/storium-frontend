.PHONY: test

venv:
	# Need to install pip separately into the venv for Debian/Ubuntu systems
	test -d venv || { python3 -m venv venv --without-pip && . venv/bin/activate; \
		wget https://bootstrap.pypa.io/get-pip.py -O venv/bin/get-pip.py && \
		chmod u+x venv/bin/get-pip.py && venv/bin/get-pip.py; }
	ls .activate.sh > /dev/null || ln -s venv/bin/activate .activate.sh
	echo "deactivate" > .deactivate.sh

install: venv
	. venv/bin/activate; pip install --verbose .[all]

test: install requirements-dev.txt
	. venv/bin/activate; pip install -r requirements-dev.txt && coverage run -m pytest -v

clean:
	rm -rf venv pygmy.egg-info build dist .coverage .pytest_cache .activate.sh \
		.mypy_cache docker-stack.yml
	find . -iname "*.pyc" -delete

deploy-%: src docker-compose.shared.yml docker-compose.%.yml
	test -d build/$* && rm -rf build/$* || true
	mkdir build/$*
	docker-compose \
		-f docker-compose.shared.yml \
		-f docker-compose.$*.yml \
		config > build/$*/docker-compose.yml
	docker-compose -f build/$*/docker-compose.yml down -v --remove-orphans
	docker-compose -f build/$*/docker-compose.yml build
	docker-compose -f build/$*/docker-compose.yml up -d

shutdown-%: build/%
	docker-compose -f build/$*/docker-compose.yml down -v --remove-orphans
