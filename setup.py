#!python
# -*- coding: UTF-8 -*-

"""
Setup script for building sqlautocode
"""

version = '0.6b1'

from setuptools import setup, find_packages

setup (name = 'sqlautocode',
		version = version,
		description = 'AutoCode is a flexible tool to autogenerate a model from an existing database.',
		author = 'Simon Pamies',
		author_email = 's.pamies@banality.de',
		url = 'http://code.google.com/p/sqlautocode/',
		packages = find_packages(exclude=['ez_setup', 'tests']),
		zip_safe=True,
		license = 'MIT',
		classifiers = [
			"Development Status :: 4 - Beta",
			"Intended Audience :: Developers",
			"Programming Language :: Python",
		],
		entry_points = dict(
			console_scripts = [
				'sqlautocode = sqlautocode.main:main',
			],
		),
		install_requires=[
                    'sqlalchemy'
		],
        include_package_data=True,
		extras_require = {
		},
		dependency_links = [
		],
		tests_require=[
			'nose>=0.10',
		],
		test_suite = "nose.collector",
	)
