PYTHON ?= python3
.PHONY: build test package preview clean
build:
	$(PYTHON) scripts/build.py
test: build
	$(PYTHON) -m unittest discover -s tests -v
package: test
	$(PYTHON) scripts/package.py
preview: build
	$(PYTHON) scripts/preview.py
clean:
	$(PYTHON) -c 'import shutil; shutil.rmtree("build", ignore_errors=True); shutil.rmtree("dist", ignore_errors=True)'

.PHONY: limine-package limine-preview
limine-package:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) scripts/limine_build.py
limine-preview: limine-package
	$(PYTHON) scripts/limine_preview.py

.PHONY: setup-package
setup-package: build
	$(PYTHON) scripts/limine_build.py
	$(PYTHON) scripts/setup_package.py
