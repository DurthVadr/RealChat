import unittest
import socket
import threading
import time
import rsa
import pickle
import bcrypt

from unittest.mock import patch, Mock

from server import hash_password, check_password, handle_client, handle_voice_messages, receive

class CustomTextTestResult(unittest.TextTestResult):
    def addFailure(self, test, err):
        super().addFailure(test, err)
        # Print additional information about the failure
        print(f"FAILURE in {test.id()}: {err}")

class TestServerFunctions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = "192.168.1.196"
        cls.port = 9999

        cls.server_stop_event = threading.Event()
        cls.server_thread = threading.Thread(target=receive, args=(cls.server_stop_event,))
        cls.server_thread.start()
        time.sleep(1)  # Give the server some time to start

    @classmethod
    def tearDownClass(cls):
        cls.server_stop_event.set()  # Signal the server to stop
        cls.server_thread.join()


    def setUp(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

        self.public_key, self.private_key = rsa.newkeys(1024)
        self.client_socket.send(self.public_key.save_pkcs1())

    def tearDown(self):
        self.client_socket.close()

    def run(self, result=None):
        if result is None:
            result = self.defaultTestResult()
        return super().run(result)

    def test_hash_password(self):
        hashed_password = hash_password("testpassword")
        self.assertTrue(bcrypt.checkpw("testpassword".encode("utf-8"), hashed_password))
        print("test_hash_password passed")

    def test_check_password(self):
        hashed_password = bcrypt.hashpw("testpassword".encode("utf-8"), bcrypt.gensalt())
        self.assertTrue(check_password("testpassword", hashed_password))
        self.assertFalse(check_password("wrongpassword", hashed_password))
        print("test_check_password passed")

    def test_handle_client(self):
        client_mock = Mock()
        client_mock.recv.return_value = "/login testuser testpassword".encode()

        with patch("server.broadcast") as mock_broadcast:
            with patch("server.authenticate_user", return_value=True) as mock_authenticate:
                handle_client(client_mock)

        mock_broadcast.assert_called_once_with("testuser has joined the chat!")
        print("test_handle_client passed")

    def test_handle_voice_messages(self):
        client_mock = Mock()
        client_mock.recv.return_value = b"voice_message"

        with patch("server.broadcast") as mock_broadcast:
            handle_voice_messages(client_mock)

        mock_broadcast.assert_called_once_with("Voice Message from mock:<10: voice_message")
        print("test_handle_voice_messages passed")

    def test_receive(self):
        server_mock = Mock()
        server_mock.accept.return_value = (Mock(), "mock_address")
        server_mock.recv.side_effect = [
            rsa.PublicKey.save_pkcs1().decode(),
            "testuser".encode(),
            "testpassword".encode()
        ]

        with patch("server.broadcast") as mock_broadcast:
            with patch("server.authenticate_user", return_value=True) as mock_authenticate:
                receive()

        mock_broadcast.assert_called_once_with("testuser has joined the chat!")

if __name__ == "__main__":
    # Use CustomTextTestResult for more control over the output
    unittest.TextTestRunner(resultclass=CustomTextTestResult).run(unittest.TestLoader().loadTestsFromTestCase(TestServerFunctions))
