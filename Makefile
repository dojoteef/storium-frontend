username = $(shell whoami)

.PHONY: test $(wildcard build-%) $(wildcard shutdown-%) \
	$(wildcard deploy-%) $(wildcard redeploy-%)

venv:
	# Need to install pip separately into the venv for Debian/Ubuntu systems
	test -d venv || { python3 -m venv venv --without-pip && . venv/bin/activate; \
		wget https://bootstrap.pypa.io/get-pip.py -O venv/bin/get-pip.py && \
		chmod u+x venv/bin/get-pip.py && venv/bin/get-pip.py; }
	ls .activate.sh > /dev/null || ln -s venv/bin/activate .activate.sh
	echo "deactivate" > .deactivate.sh

venv-base: venv
	. venv/bin/activate; pip install -e .[sqlite,scipy,build]

venv-dev: venv-base requirements-dev.txt
	. venv/bin/activate; pip install -r requirements-dev.txt

lint: venv-dev
	. venv/bin/activate; mypy src; pylint -d W0511 src

test: venv-dev
	. venv/bin/activate; coverage run -m pytest -v

clean:
	rm -rf venv .pytest_cache .activate.sh .mypy_cache
	find . -iname "*.pyc" -delete

buildvars-%:
	$(eval build_tag = $(*:dev=dev-$(username)))
	$(eval build_dir = build/$(build_tag))
	$(eval project_name = woolgatherer_$(build_tag))

build-%: venv-base buildvars-% src docker-compose.shared.yml docker-compose.%.yml
	test -d $(build_dir) && rm -rf $(build_dir) || true
	mkdir -p $(build_dir)
	docker-compose \
		-f docker-compose.shared.yml \
		-f docker-compose.$*.yml \
		$$(test -f docker-compose.env.yml && echo -f docker-compose.env.yml || echo "") \
		$$(test -f docker-compose.$*.env.yml && echo -f docker-compose.$*.env.yml || echo "") \
		config > $(build_dir)/docker-compose.yml
	sed -i "s/image: woolgatherer/\0:$(build_tag)/g" $(build_dir)/docker-compose.yml
	docker-compose -f $(build_dir)/docker-compose.yml build

redeploy-%: buildvars-% shutdown-% build-%
	docker-compose -p $(project_name) -f $(build_dir)/docker-compose.yml up -d

deploy-%: buildvars-%
	docker-compose -p $(project_name) -f $(build_dir)/docker-compose.yml up -d

shutdown-%: buildvars-%
	test -f $(build_dir)/docker-compose.yml && \
		docker-compose -p $(project_name) -f $(build_dir)/docker-compose.yml down --remove-orphans || true

run-%-shell: buildvars-%
	docker-compose -p $(project_name) -f $(build_dir)/docker-compose.yml run backend sh
