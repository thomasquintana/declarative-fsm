# coding: utf-8

from setuptools import setup
import fsm

setup(
    name="declarative-fsm",
    version=fsm.__version__,
    py_modules=["fsm"],
    author="Thomas Quintana",
    author_email="quintana.thomas@gmail.com",
    description='A Python declarative finite state machine.',
    license="PROPRIETARY",
    url="https://github.com/thomasquintana/declarative-fsm",
)
