import tempfile
import re

from wonderlandClient import ModelGymClient
from wonderlandClient.modelgym_client import MODELGYM_CONFIG

class TestModelGymClient():

    def setup_class(self):
        print("\n=== TestModelGymClient - setup calss ===\n")

    def teardown_class(self):
        print("\n=== TestModelGymClient - teardown class ===\n")

    def setup(self):
        print("TestModelGymClient - setup method")

    def teardown(self):
        print("TestModelGymClient - teardown method")

    def test_connection(self):
        ModelGymClient()

    def test_afs_send_data(self):
        c = ModelGymClient()
        fs = c.file_service
        share = c.afs_share

        with tempfile.NamedTemporaryFile(mode="w") as f:
            f.write("TempData")
            afs_path = c.send_data(f.name, push_data=True)
            assert(re.match('DATA/[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}\.[0-9]{2}-[0-9A-Za-z]{10}/data.csv', afs_path))
            assert(fs.exists(share_name=share,
                              directory_name=afs_path.parent,
                              file_name=afs_path.name))

        fs.delete_file(share_name=share,
                        directory_name=afs_path.parent,
                        file_name=afs_path.name)
