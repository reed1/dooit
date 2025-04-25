from dooit.api import manager
import pytest

TEMP_PATH = ":memory:"


class CoreTestBase:
    @pytest.fixture(scope="class")
    def session(self):
        manager.connect(TEMP_PATH)
        yield manager.session
        manager.session.rollback()
        manager.session.close()

    @pytest.fixture(autouse=True)
    def setup_teardown(self, session):
        self.session = session
        yield
        self.session.rollback()
        self.session.close()
