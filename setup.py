#!/usr/bin/env python
"""Setup script for installation
"""
from setuptools import setup

setup(
    name='test-event-gen',
    version='0.0.1',
    description='Audit event generator',
    author='Freddie Mather',
    author_email='freddie.mather@smartdcs.co.uk',
    packages=[
        'test_event_generator',
        'test_event_generator.core',
        'test_event_generator.utils'
    ],
)
