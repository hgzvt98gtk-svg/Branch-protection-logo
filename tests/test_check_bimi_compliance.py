import socket
import sys
import unittest
from collections import namedtuple
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_bimi_compliance as checker


TLSResult = namedtuple("TLSResult", ("socket", "is_verified"))


def address_info(address):
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    return [(family, socket.SOCK_STREAM, 6, "", (address, 443))]


class CheckHttpsTests(unittest.TestCase):
    def test_rejects_non_public_ipv4_and_ipv6_addresses(self):
        for address in ("10.0.0.1", "127.0.0.1", "169.254.1.1", "::1", "fc00::1", "fe80::1"):
            with self.subTest(address=address):
                errors = []
                with patch.object(checker.socket, "getaddrinfo", return_value=address_info(address)):
                    self.assertIsNone(checker.check_https("https://logo.example/logo.svg", errors))
                self.assertTrue(errors)
                self.assertIn("public IP addresses", errors[0])

    def test_rejects_hostname_with_mixed_public_and_private_answers(self):
        answers = address_info("8.8.8.8") + address_info("10.0.0.1")
        errors = []
        with patch.object(checker.socket, "getaddrinfo", return_value=answers):
            self.assertIsNone(checker.check_https("https://logo.example/logo.svg", errors))
        self.assertIn("public IP addresses", errors[0])

    def test_pins_public_address_and_keeps_hostname_for_tls(self):
        errors = []
        with patch.object(checker.socket, "getaddrinfo", return_value=address_info("8.8.8.8")):
            checked = checker.check_https("https://logo.example:8443/logo.svg", errors)
        self.assertEqual(errors, [])
        prepared_url, pinned_ip = checked
        self.assertEqual(prepared_url, "https://logo.example:8443/logo.svg")

        adapter = checker.PinnedHTTPSAdapter("logo.example", 8443, pinned_ip)
        try:
            connection = adapter.pool._new_conn()
            self.assertEqual(connection.host, "logo.example")
            self.assertEqual(connection.server_hostname, "logo.example")
            self.assertEqual(connection.assert_hostname, "logo.example")
            self.assertEqual(connection.pinned_ip, "8.8.8.8")

            connection.sock = MagicMock()
            connection.putrequest("GET", "/logo.svg")
            connection.endheaders()
            self.assertIn(b"Host: logo.example:8443\r\n", connection.sock.sendall.call_args.args[0])

            with patch.object(checker.urllib3_connection, "create_connection", return_value=MagicMock()):
                with patch(
                    "urllib3.connection._ssl_wrap_socket_and_match_hostname",
                    return_value=TLSResult(MagicMock(), True),
                ) as wrap_tls:
                    connection.connect()
            self.assertEqual(wrap_tls.call_args.kwargs["server_hostname"], "logo.example")
            self.assertEqual(wrap_tls.call_args.kwargs["assert_hostname"], "logo.example")
        finally:
            adapter.close()

    def test_dns_change_after_validation_cannot_change_connected_address(self):
        errors = []
        with patch.object(checker.socket, "getaddrinfo", return_value=address_info("8.8.8.8")):
            checked = checker.check_https("https://logo.example/logo.svg", errors)
        prepared_url, pinned_ip = checked

        adapter = checker.PinnedHTTPSAdapter("logo.example", 443, pinned_ip)
        try:
            connection = adapter.pool._new_conn()
            with patch.object(checker.socket, "getaddrinfo", return_value=address_info("127.0.0.1")):
                with patch.object(checker.urllib3_connection, "create_connection") as connect:
                    connection._new_conn()
            self.assertEqual(connect.call_args.args[0], ("8.8.8.8", 443))
        finally:
            adapter.close()

    def test_adapter_rejects_other_hosts_and_proxies(self):
        adapter = checker.PinnedHTTPSAdapter("logo.example", 443, "8.8.8.8")
        try:
            with self.assertRaises(checker.requests.exceptions.InvalidURL):
                adapter.get_connection("https://other.example/logo.svg")
            with self.assertRaises(checker.requests.exceptions.InvalidURL):
                adapter.get_connection("https://logo.example/logo.svg", {"https": "http://proxy.example"})
        finally:
            adapter.close()


if __name__ == "__main__":
    unittest.main()
