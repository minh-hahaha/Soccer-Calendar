"""Minimal application package used for testing.

The original repository structures the backend code under the
``backend`` package.  The test-suite, however, imports modules from an
``app`` package.  To keep the production code untouched while allowing
the tests to run, this lightweight package simply re-exports the pieces
the tests expect.
"""

# The submodules are populated in their respective files.  Nothing is
# required at the package level beyond making it a proper Python package.

