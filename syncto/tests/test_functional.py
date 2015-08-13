import mock
from uuid import uuid4

from cliquet.errors import ERRORS
from cliquet.tests.support import FormattedErrorMixin

from syncto import AUTHORIZATION_HEADER, CLIENT_STATE_HEADER

from .support import BaseWebTest, unittest


COLLECTION_URL = "/buckets/syncto/collections/tabs/records"
RECORD_URL = "/buckets/syncto/collections/tabs/records/%s" % uuid4()


class FunctionalTest(FormattedErrorMixin, BaseWebTest, unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(FunctionalTest, self).__init__(*args, **kwargs)

    def test_authorization_header_is_required_for_collection(self):
        resp = self.app.get(COLLECTION_URL, headers=self.headers, status=401)

        self.assertFormattedError(
            resp, 401, ERRORS.MISSING_AUTH_TOKEN, "Unauthorized",
            "Provide a BID assertion %s header." % AUTHORIZATION_HEADER)

    def test_client_state_header_is_required_for_collection(self):
        headers = self.headers.copy()
        headers['Authorization'] = "BrowserID abcd"
        resp = self.app.get(COLLECTION_URL, headers=headers, status=401)

        self.assertFormattedError(
            resp, 401, ERRORS.MISSING_AUTH_TOKEN, "Unauthorized",
            "Provide the tokenserver %s header." % CLIENT_STATE_HEADER)

    def test_authorization_header_is_required_for_records(self):
        resp = self.app.get(RECORD_URL, headers=self.headers, status=401)

        self.assertFormattedError(
            resp, 401, ERRORS.MISSING_AUTH_TOKEN, "Unauthorized",
            "Provide a BID assertion %s header." % AUTHORIZATION_HEADER)

    def test_client_state_header_is_required_for_records(self):
        headers = self.headers.copy()
        headers['Authorization'] = "BrowserID abcd"
        resp = self.app.get(RECORD_URL, headers=headers, status=401)

        self.assertFormattedError(
            resp, 401, ERRORS.MISSING_AUTH_TOKEN, "Unauthorized",
            "Provide the tokenserver %s header." % CLIENT_STATE_HEADER)


class CollectionTest(FormattedErrorMixin, BaseWebTest, unittest.TestCase):

    def setUp(self):
        self.headers.update({
            AUTHORIZATION_HEADER: "BrowserID abcd",
            CLIENT_STATE_HEADER: "1234",
            'Origin': 'http://localhost:8000'
        })
        p = mock.patch("syncto.views.collection.build_sync_client")
        self.sync_client = p.start()
        self.sync_client.return_value._authenticate.return_value = None
        self.sync_client.return_value.get_records.return_value = [{
            "id": "Y_-5-LEeQBuh60IT0MyWEQ",
            "modified": 14377478425.69
        }]
        headers = {}
        headers['X-Last-Modified'] = '14377478425.69'
        headers['X-Weave-Records'] = '1'
        headers['X-Weave-Next-Offset'] = '12345'
        self.sync_client.return_value.raw_resp.headers = headers

        self.addCleanup(p.stop)

    def test_collection_handle_cors_headers(self):
        resp = self.app.get(COLLECTION_URL,
                            headers=self.headers, status=200)
        self.assertIn('Access-Control-Allow-Origin', resp.headers)

    def test_collection_handle_since_parameter(self):
        self.app.get(COLLECTION_URL,
                     params={'_since': '14377478425700',
                             '_sort': 'newest'},
                     headers=self.headers, status=200)
        self.sync_client.return_value.get_records.assert_called_with(
            "tabs", full=True, newer='14377478425700', sort='newest')

    def test_collection_handle_limit_and_token_parameters(self):
        self.app.get(COLLECTION_URL,
                     params={'_limit': '2', '_token': '12345',
                             '_sort': 'index'},
                     headers=self.headers, status=200)
        self.sync_client.return_value.get_records.assert_called_with(
            "tabs", full=True, limit='2', offset='12345', sort='index')

    def test_collection_raises_with_invalid_sort_parameter(self):
        resp = self.app.get(COLLECTION_URL,
                            params={'_sort': 'unknown'},
                            headers=self.headers, status=400)

        self.assertFormattedError(
            resp, 400, ERRORS.INVALID_PARAMETERS, "Invalid parameters",
            "_sort should be one of ('-last_modified', 'newest', "
            "'-sortindex', 'index')")

    def test_collection_can_validate_a_list_of_specified_ids(self):
        self.app.get(COLLECTION_URL,
                     params={'ids': '123,456,789'},
                     headers=self.headers, status=200)


class RecordTest(BaseWebTest, unittest.TestCase):

    def setUp(self):
        self.headers.update({
            AUTHORIZATION_HEADER: "BrowserID abcd",
            CLIENT_STATE_HEADER: "1234",
            'Origin': 'http://localhost:8000'
        })
        p = mock.patch("syncto.views.record.build_sync_client")
        self.sync_client = p.start()
        self.sync_client.return_value._authenticate.return_value = None
        self.sync_client.return_value.get_record.return_value = {
            "id": "Y_-5-LEeQBuh60IT0MyWEQ",
            "modified": 14377478425.69
        }

        self.addCleanup(p.stop)

    def test_record_handle_cors_headers(self):
        resp = self.app.get(RECORD_URL, headers=self.headers, status=200)
        self.assertIn('Access-Control-Allow-Origin', resp.headers)
