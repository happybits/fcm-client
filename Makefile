PATH := ./redis-git/src:${PATH}



help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo "  clean           remove temporary files created by build tools"
	@echo "  cleanmeta       removes all META-* and egg-info/ files created by build tools"	
	@echo "  cleancov        remove all files related to coverage reports"
	@echo "  cleanall        all the above + tmp files from development tools"
	@echo "  test            run test suite"
	@echo "  sdist           make a source distribution"
	@echo "  bdist           make an egg distribution"
	@echo "  install         install package"
	@echo "  publish         publish package to pypi"
	@echo " *** CI Commands ***"
	@echo "  test            starts/activates the test cluster nodes and runs tox test"
	@echo "  tox             run all tox environments and combine coverage report after"

clean:
	-rm -f MANIFEST
	-rm -rf dist/
	-rm -rf build/

cleancov:
	-rm -rf htmlcov/
	-coverage combine
	-coverage erase

cleanmeta:
	-rm -rf *.egg-info/

cleantox:
	-rm -rf .tox/

cleanall: clean cleancov cleanmeta cleantox

sdist: cleanmeta
	python setup.py sdist

bdist: cleanmeta
	python setup.py bdist_egg

install:
	python setup.py install

publish:
	./publish.sh

local:
	python setup.py build_ext --inplace

test:
	make tox

tox:
	coverage erase
	tox
	coverage combine
	coverage report

.PHONY: test
